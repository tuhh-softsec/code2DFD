import ast
import os
from pathlib import Path

import core.file_interaction as fi
from output_generators.logger import logger
import core.parse_files as parse
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def set_microservices(dfd) -> dict:
    """Extracts the list of services from build.gradle files and sets the variable in the tmp-file.
    """

    if not used_in_application():
        return False

    if tmp.tmp_config.has_option("DFD", "microservices"):
        microservices = ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])
    else:
        microservices = dict()

    gradle_files = fi.get_file_as_lines("build.gradle")
    for gf in gradle_files.keys():
        gradle_file = gradle_files[gf]
        image = "image_placeholder"
        if not gradle_file["path"] == "build.gradle":       # root gradle file, not for a service

            microservice, properties = parse_configurations(gradle_file)

            if microservice[0]:
                try:
                    id = max(microservices.keys()) + 1
                except:
                    id = 0
                microservices[id] = dict()

                microservices[id]["name"] = microservice[0]
                microservices[id]["image"] = image
                microservices[id]["type"] = "internal"
                microservices[id]["gradle_path"] = gradle_file["path"]
                microservices[id]["properties"] = properties
                microservices[id]["stereotype_instances"] = list()
                microservices[id]["tagged_values"] = list()

                try:
                    trace = dict()
                    name = microservice[0]
                    trace["item"] = name
                    trace["file"] = microservice[1][0]
                    trace["line"] = microservice[1][1]
                    trace["span"] = microservice[1][2]
                    traceability.add_trace(trace)
                except:
                    pass

    tmp.tmp_config.set("DFD", "microservices", str(microservices).replace("%", "%%"))

    return microservices


def used_in_application() -> bool:
    """Checks if application has build.gradle file.
    """

    return fi.file_exists("build.gradle")


def parse_configurations(gradle_file) -> str:
    """Extracts servicename and properties for a given file.
    """

    properties = set()
    microservice, properties = parse_properties_file(gradle_file["path"])

    if microservice[0]:
        return microservice, properties
    return (False, False), properties


def parse_properties_file(gradle_path: str):
    """Goes down folder structure to find properties file. Then tries to extract servicename. Else returns False.
    """

    properties = set()
    microservice = [False, False]
    # find properties file
    path = os.path.dirname(gradle_path)

    local_repo_path = tmp.tmp_config["Repository"]["local_path"]

    dirs = list()
    dirs.append(os.scandir(os.path.join(local_repo_path, path)))

    while dirs:
        dir = dirs.pop()
        for entry in dir:
            if entry.is_file():
                if not "test" in entry.path:
                    filename = os.path.basename(entry.path)
                    if filename in ["application.properties", "bootstrap.properties"]:
                        logger.info("Found application.properties here: " + str(entry.path))
                        file_path = os.path.relpath(entry.path, start=local_repo_path)
                        new_microservice, new_properties = parse.parse_properties_file(file_path)
                        if new_microservice[0]:
                            microservice = new_microservice
                        if new_properties:
                            properties = properties.union(new_properties)
                    elif filename in ["application.yaml", "application.yml", "bootstrap.yml", "bootstrap.yaml", "filebeat.yml", "filebeat.yaml"]:
                        logger.info("Found properties file here: " + str(entry.path))
                        file_path = os.path.relpath(entry.path, start=local_repo_path)
                        new_microservice, new_properties = parse.parse_yaml_file(file_path)
                        if new_microservice[0]:
                            microservice = new_microservice
                        if new_properties:
                            properties = properties.union(new_properties)
            elif entry.is_dir():
                dirs.append(os.scandir(entry.path))

    return microservice, properties


def detect_microservice(file_path, dfd):
    """Detects which microservice a file belongs to by looking for next build.gradle.
    """

    if not used_in_application():
        return False

    microservice = [False, False]
    microservices = tech_sw.get_microservices(dfd)


    found_gradle = False

    local_repo_path = tmp.tmp_config["Repository"]["local_path"]

    dirs = list()
    path = os.path.dirname(file_path)
    while not found_gradle and path != "":
        dirs.append(os.scandir(os.path.join(local_repo_path, path)))
        while dirs:
            dir = dirs.pop()
            for entry in dir:
                if entry.is_file():
                    if os.path.basename(entry.path).casefold() == "build.gradle":
                        logger.info("Found build.gradle here: " + str(entry.path))
                        gradle_path = os.path.relpath(entry.path, start=local_repo_path)
                        found_gradle = True
        path = os.path.dirname(path)

    if found_gradle:
        gradle_file = dict()
        gradle_file["path"] = gradle_path
        for m in microservices.keys():
            try:
                if microservices[m]["gradle_path"] == gradle_path:
                    microservice[0] = microservices[m]["name"]
            except:
                pass
        if not microservice[0]:

            gradle_file["content"] = fi.file_as_lines(gradle_path)
            microservice, properties = parse_configurations(gradle_file)
    else:
        logger.info("Did not find microservice")

    if not microservice[0]:

        for m in microservices.keys():
            try:
                image = microservices[m]["image"]
                path = os.path.dirname(file_path)
                if image in path:
                    microservice[0] = microservices[m]["name"]
            except:
                pass

    return microservice[0]
