import ast
import os
import re

import core.file_interaction as fi
import output_generators.logger as logger
import core.parse_files as parse
import core.technology_switch as tech_sw
import technology_specific_extractors.docker.dcr_entry as dcr
import tmp.tmp as tmp
import output_generators.traceability as traceability
from core.service import CService


def set_microservices(dfd) -> dict:
    """Extracts the list of services from pom.xml files and sets the variable in the tmp-file.
    """

    if not used_in_application():
        return False

    if tmp.tmp_config.has_option("DFD", "microservices"):
        microservices = ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])
    else:
        microservices = dict()
    microservices_set = set()

    pom_files = fi.get_file_as_lines("pom.xml")
    module_tuples = list()

    for pf in pom_files.keys():
        pom_file = pom_files[pf]
        image = "image_placeholder"
        modules = extract_modules(pom_file)
        if modules:
            module_tuples.append((pom_file["name"], modules))
        else:
            microservice, properties = parse_configurations(pom_file)
            properties = extract_dependencies(properties, pom_file["content"])
            if microservice[0]:
                port = dcr.detect_port(pom_file["path"])
                # create microservice in dict
                try:
                    id = max(microservices.keys()) + 1
                except:
                    id = 0
                microservices[id] = dict()

                microservices[id]["servicename"] = microservice[0]
                microservices[id]["image"] = image
                microservices[id]["type"] = "internal"
                microservices[id]["pom_path"] = pom_file["path"]
                microservices[id]["properties"] = properties
                microservices[id]["stereotype_instances"] = list()
                if port:
                    microservices[id]["tagged_values"] = [("Port", port)]
                else:
                    microservices[id]["tagged_values"] = list()

                new_service = CService(microservice[0], )
                try:
                    trace = dict()
                    name = microservice[0]
                    name = name.replace("pom_", "")
                    trace["item"] = name
                    trace["file"] = microservice[1][0]
                    trace["line"] = microservice[1][1]
                    trace["span"] = microservice[1][2]
                    traceability.add_trace(trace)
                except:
                    pass

    nested_microservices = check_nested_modules(module_tuples)
    for m in nested_microservices:
        microservices_set.add(m)

    tmp.tmp_config.set("DFD", "microservices", str(microservices))

    return microservices


def extract_dependencies(properties: set, pom_file_lines) -> set:
    """Parses pom_file to check for dependencies.
    """

    for line in pom_file_lines:
        if "spring-cloud-starter-netflix-hystrix" in line:
            properties.add(("circuit_breaker", "Hystrix", ("file", "line", "span")))

    return properties


def used_in_application() -> bool:
    """Checks if application has pom.xml file.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]

    return fi.file_exists("pom.xml", repo_path)


def extract_modules(file: list) -> list:
    """Extracts modules of a Maven project based on the <module> </module>-tag.
    """

    modules = list()
    for line in file["content"]:
        if "<module>" in line:
            modules.append(line.split("<module>")[1].split("</module>")[0].strip())

    return modules


def check_nested_modules(module_tuples: list) -> list:
    """Takes list of tuples of the form [(component, [modules])] and checks for links between them. If yes, returns list of components = services that need to be added to the list.
    """

    microservices = list()
    for tuple1 in module_tuples:
        for tuple2 in module_tuples:
            if tuple1[0] in tuple2[1]:
                microservices.append(tuple1[0])

    return microservices


def parse_configurations(pom_file) -> str:
    """Extracts servicename and properties for a given file. Tries properties file first, then pom file.
    """

    properties = set()
    microservice, properties = parse_properties_file(pom_file["path"])
    if not microservice[0]:
        microservice = extract_servicename_pom_file(pom_file["content"], pom_file["path"])

        if microservice[0]:
            microservice[0] = "pom_" + microservice[0]
    if microservice[0]:
        return microservice, properties

    return (False, False), properties


def parse_properties_file(pom_path: str):
    """Goes down folder structure to find properties file. Then tries to extract servicename. Else returns False.
    """

    properties = set()
    microservice = [False, False]
    # find properties file
    repo_path = tmp.tmp_config["Repository"]["path"]
    path = ("/").join(pom_path.split("/")[:-1])

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    dirs = list()
    dirs.append(os.scandir(local_repo_path + "/" + path))

    while dirs:
        dir = dirs.pop()
        for entry in dir:
            if entry.is_file():
                if not "test" in entry.path:
                    if entry.path.split("/")[-1] in ["application.properties", "bootstrap.properties"]:
                        logger.write_log_message("Found application.properties here: " + str(entry.path), "info")
                        file_path = entry.path
                        file_url = "https://raw.githubusercontent.com/" + repo_path + "/master/" + ("/").join(file_path.split("/")[3:])
                        new_microservice, new_properties = parse.parse_properties_file(file_url)
                        if new_microservice[0]:
                            microservice = new_microservice
                        if new_properties:
                            properties = properties.union(new_properties)
                    elif entry.path.split("/")[-1] in ["application.yaml", "application.yml", "bootstrap.yml", "bootstrap.yaml", "filebeat.yml", "filebeat.yaml"]:
                        logger.write_log_message("Found properties file here: " + str(entry.path), "info")
                        file_path = entry.path
                        file_url = "https://raw.githubusercontent.com/" + repo_path + "/master/" + ("/").join(file_path.split("/")[3:])
                        new_microservice, new_properties = parse.parse_yaml_file(file_url, file_path)
                        if new_microservice[0]:
                            microservice = new_microservice
                        if new_properties:
                            properties = properties.union(new_properties)
            elif entry.is_dir():
                dirs.append(os.scandir(entry.path))

    return microservice, properties


def extract_servicename_pom_file(pom_file: list, file_name: str) -> str:
    """Extracts the name of a Maven-module based on the <finalName> tag if existing, else the <artifactIf>.
    """

    microservice = [False, False]
    found_finalName = False
    for line_nr in range(len(pom_file)):
        line = pom_file[line_nr]
        if "<finalName>" in line:
            microservice[0] = line.split("<finalName>")[1].split("</finalName>")[0].strip()

            # traceability
            line_number = line_nr + 1
            length_tuple = re.search(microservice[0], line).span()
            span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
            trace = (file_name, line_number, span)
            microservice[1] = trace

            found_finalName = True
    if not found_finalName:
        for line_nr in range(len(pom_file)):
            line = pom_file[line_nr]
            if "<artifactId>" in line:
                if not in_dependency(pom_file, line_nr) and not in_parent(pom_file, line_nr) and not in_plugin(pom_file, line_nr):
                    microservice[0] = line.split("<artifactId>")[1].split("</artifactId>")[0].strip()

                    # traceability
                    line_number = line_nr + 1
                    length_tuple = re.search(microservice[0], line).span()
                    span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                    trace = (file_name, line_number, span)
                    microservice[1] = trace

    return microservice


def in_dependency(file: list, line_nr: str) -> bool:
    """Checks if provided line is inside a <dependency> </dependency> block in the pom.xml .
    """

    count = line_nr
    while count >= 0:
        if "<dependency>" in file[count] and "</dependency>" in file[count]:
            return False
        if "<dependency>" in file[count]:
            return True
        if "</dependency>" in file[count]:
            return False
        count -= 1
    return False


def in_parent(file: list, line_nr: str) -> bool:
    """Checks if provided line is inside a <plugin> </parent> block in the pom.xml .
    """

    count = line_nr
    while count >= 0:
        if "<parent>" in file[count] and "</parent>" in file[count]:
            return False
        if "<parent>" in file[count]:
            return True
        if "</parent>" in file[count]:
            return False
        count -= 1
    return False


def in_plugin(file: list, line_nr: str) -> bool:
    """Checks if provided line is inside a <plugin> </plugin> block in the pom.xml .
    """

    count = line_nr
    while count >= 0:
        if "<plugin>" in file[count] and "</plugin>" in file[count]:
            return False
        if "<plugin>" in file[count]:
            return True
        if "</plugin>" in file[count]:
            return False
        count -= 1
    return False


def in_comment(file:list, line_nr: str) -> bool:
    """Checks if provided line is inside a comment block in the pom.xml .
    """

    count = line_nr
    while count >= 0:
        if "<--" in file[count] and "-->" in file[count]:
            return False
        if "<--" in file[count]:
            return True
        if "-->" in file[count]:
            return False
        count -= 1
    return False


count = 0

def detect_microservice(file_path, dfd):
    """Detects which microservice a file belongs to by looking for next pom.xml.
    """

    if not used_in_application():
        return False

    microservice = [False, False]
    microservices = tech_sw.get_microservices(dfd)

    repo_path = tmp.tmp_config["Repository"]["path"]

    path = file_path
    found_pom = False

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    dirs = list()
    path = ("/").join(path.split("/")[:-1])
    while not found_pom and path != "":
        dirs.append(os.scandir(local_repo_path + "/" + path))
        while dirs:
            dir = dirs.pop()
            for entry in dir:
                if entry.is_file():
                    if entry.name.casefold() == "pom.xml":
                        pom_path = ("/").join(entry.path.split("/")[3:])
                        logger.write_log_message("Found pom.xml here: " + str(entry.path), "info")
                        found_pom = True
                        pom_file_url = "https://raw.githubusercontent.com/" + repo_path + "/master/" + ("/").join(file_path.split("/")[3:])
        path = ("/").join(path.split("/")[:-1])

    if found_pom:
        pom_file = dict()
        pom_file["path"] = pom_path
        for m in microservices.keys():
            try:
                if microservices[m]["pom_path"] == pom_path:
                    microservice[0] = microservices[m]["servicename"]
            except:
                pass
        if not microservice[0]:
            pom_file["content"] = fi.file_as_lines(pom_file_url)
            microservice, properties = parse_configurations(pom_file)
    else:
        logger.write_log_message("Did not find microservice", "info")

    if not microservice[0]:

        for m in microservices.keys():
            try:
                image = microservices[m]["image"]
                path = "/".join(file_path.split("/")[:-1])
                path = path.strip(".").strip("/")
                image = image.strip(".").strip("/")
                if image in path:
                    microservice[0] = microservices[m]["servicename"]
            except:
                pass

    return microservice[0]
