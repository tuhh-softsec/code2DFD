import ast
import os

import core.file_interaction as fi
import output_generators.logger as logger
import core.parse_files as parse
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability

from core.DFD import CDFD
from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow

def detect_gradle(dfd: CDFD) -> dict:
    """Extracts the list of services from build.gradle files and sets the variable in the tmp-file.
    """

    if not used_in_application(dfd):
        return False

    gradle_files = fi.get_file_as_lines("build.gradle")
    for gf in gradle_files.keys():
        gradle_file = gradle_files[gf]
        if not gradle_file["path"] == "build.gradle":       # root gradle file, not for a service

            microservice, properties = parse_configurations(gradle_file)

            if microservice[0]:
                # microservices[id]["gradle_path"] = gradle_file["path"]

                dfd.add_service(CService(microservice[0], list(), list(), properties))

    return 


def used_in_application(dfd: CDFD) -> bool:
    """Checks if application has build.gradle file.
    """

    return fi.file_exists("build.gradle", dfd.repo_path)


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
    repo_path = tmp.tmp_config["Repository"]["path"]
    path = ("/").join(gradle_path.split("/")[:-1])

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    dirs = list()
    dirs.append(os.scandir(local_repo_path + "/" + path))

    while dirs:
        dir = dirs.pop()
        for entry in dir:
            if entry.is_file():
                if not "test" in entry.path:
                    if entry.path.split("/")[-1] in ["application.properties", "bootstrap.properties"]:
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


def detect_microservice(file_path: str, dfd: CDFD) -> str:
    """Detects which microservice a file belongs to by looking for next build.gradle.
    """

    if not used_in_application(dfd):
        return False

    detected_microservice = False

    path = file_path
    found_gradle = False

    local_repo_path = "./analysed_repositories/" + ("/").join(dfd.repo_path.split("/")[1:])

    dirs = list()
    path = ("/").join(path.split("/")[:-1])
    while not found_gradle and path != "":
        dirs.append(os.scandir(local_repo_path + "/" + path))
        while dirs:
            dir = dirs.pop()
            for entry in dir:
                if entry.is_file():
                    if entry.name.casefold() == "build.gradle":
                        gradle_path = ("/").join(entry.path.split("/")[3:])
                        found_gradle = True
                        gradle_file_url = "https://raw.githubusercontent.com/" + dfd.repo_path + "/master/" + file_path
        path = ("/").join(path.split("/")[:-1])

    if found_gradle:
        gradle_file = dict()
        gradle_file["path"] = gradle_path
        for service in dfd.services:
            if "gradle_path" in service.properties:
                if service.properties["gradle_path"] == gradle_path:
                    detected_microservice = service.name
        if not detected_microservice:
            gradle_file["content"] = fi.file_as_lines(gradle_file_url)
            microservice, properties = parse_configurations(gradle_file)
            detected_microservice = microservice[0]

    if not detected_microservice:
        for service in dfd.services:
            try:
                image = service.properties["image"]
                path = "/".join(file_path.split("/")[:-1])
                path = path.strip(".").strip("/")
                image = image.strip(".").strip("/")
                if image in path:
                    detected_microservice = service.name
            except:
                pass

    return detected_microservice


#
