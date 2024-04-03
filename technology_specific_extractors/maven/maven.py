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

from core.DFD import CDFD
from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow


def detect_maven(dfd: CDFD) -> dict:
    """Extracts the list of services from pom.xml files and sets the variable in the tmp-file.
    """

    if not used_in_application(dfd.repo_path):
        return False

    pom_files = fi.get_file_as_lines("pom.xml")

    for pf in pom_files.keys():
        pom_file = pom_files[pf]
        microservice, properties = parse_configurations(pom_file)
        
        if microservice[0]:
            port = dcr.detect_port(pom_file["path"])

            if port:
                tagged_values = [("Port", port)]
            else:
                tagged_values = list()

            dfd.add_service(CService(microservice[0], list(), tagged_values, properties))

    return 



def used_in_application(repo_path) -> bool:
    """Checks if application has pom.xml file.
    """

    return fi.file_exists("pom.xml", repo_path)


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
    Returns servicename
    """

    if not used_in_application(dfd.repo_path):
        return False

    detected_service = False

    path = file_path
    found_pom = False

    local_repo_path = "./analysed_repositories/" + ("/").join(dfd.repo_path.split("/")[1:])

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
                        pom_file_url = "https://raw.githubusercontent.com/" + dfd.repo_path + "/master/" + ("/").join(file_path.split("/")[3:])
        path = ("/").join(path.split("/")[:-1])

    if found_pom:
        pom_file = dict()
        pom_file["path"] = pom_path
        for service in dfd.services:
            try:
                if "pom_path" in service.properties:
                    if service.properties["pom_path"] == pom_path:
                        detected_service = service.name
            except:
                pass
        if not detected_service:
            pom_file["content"] = fi.file_as_lines(pom_file_url)
            microservice, properties = parse_configurations(pom_file)
            detected_service = microservice[0]
    
    if not detected_service:
        for service in dfd.services:
            try:
                image = service.properties["image"]
                path = "/".join(file_path.split("/")[:-1])
                path = path.strip(".").strip("/")
                image = image.strip(".").strip("/")
                if image in path:
                    detected_service = service.name
            except:
                pass

    return detected_service
