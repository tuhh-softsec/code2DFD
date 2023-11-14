import ast
import os

import core.file_interaction as fi
import output_generators.logger as logger
import core.technology_switch as tech_sw
import technology_specific_extractors.docker_compose.dcm_parser as dcm_parser
import tmp.tmp as tmp
import output_generators.traceability as traceability

docker_compose_content = False


def set_microservices(dfd) -> None:
    """Reads microservices out of a .yml file, only returns ones defined in this repo.
    """

    global docker_compose_content

    microservices_set = set()

    # Download docker-compose file
    if not docker_compose_content:
        raw_files = fi.get_file_as_yaml("docker-compose.yml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_yaml("docker-compose.yaml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_yaml("docker-compose*")
        if len(raw_files) == 0:
            microservices = tech_sw.get_microservices(dfd)
            microservices = clean_pom_names(microservices)
            tmp.tmp_config.set("DFD", "microservices", str(microservices))
            return
        docker_compose_content = raw_files[0]["content"]

    microservices_set, properties_dict = dcm_parser.extract_microservices(docker_compose_content, raw_files[0]["path"])

    if not microservices_set:
        microservices = tech_sw.get_microservices(dfd)
        microservices = clean_pom_names(microservices)
        tmp.tmp_config.set("DFD", "microservices", str(microservices))
        return
    microservices = dictionarify(microservices_set, properties_dict)
    microservices = clean_pom_names(microservices)

    tmp.tmp_config.set("DFD", "microservices", str(microservices))


def clean_pom_names(microservices: dict) -> dict:
    """Deletes "pom_" from microservice names. Needed in specific cases.
    """

    for m in microservices.keys():
        microservices[m]["servicename"] = microservices[m]["servicename"].replace("pom_", "")

    return microservices


def dictionarify(elements_set: set, properties_dict: dict) -> dict:
    """Turns set of services into dictionary.
    """

    if tmp.tmp_config.has_option("DFD", "microservices"):
        elements = ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])
    else:
        elements = dict()

    for e in elements_set:
        try:
            properties = properties_dict[e[0]]
        except:
            properties = set()
        tuple = check_image(e[1])
        if tuple:
            stereotypes = tuple[0]
            tagged_values = tuple[1]
        else:
            stereotypes = list()
            tagged_values = list()
        if e[3]:
            tagged_values.append(("Port", str(e[3][0])))
            trace = dict()
            trace["parent_item"] = e[0]#.replace("pom_", "")
            trace["item"] = "Port"
            trace["file"] = e[3][1]
            trace["line"] = e[3][2]
            trace["span"] = e[3][3]
            traceability.add_trace(trace)
        try:
            id = max(elements.keys()) + 1
        except:
            id = 0
        elements[id] = dict()

        elements[id]["servicename"] = e[0]
        elements[id]["image"] = e[1]
        elements[id]["type"] = e[2]
        elements[id]["properties"] = properties
        elements[id]["stereotype_instances"] = stereotypes
        elements[id]["tagged_values"] = tagged_values

        trace = dict()
        trace["item"] = e[0]#.replace("pom_", "")
        trace["file"] = e[4][0]
        trace["line"] = e[4][1]
        trace["span"] = e[4][2]
        traceability.add_trace(trace)

    return elements


def set_information_flows(dfd):
    """Adds information flows based on "links" parameter in docker-compose.
    """

    global docker_compose_content

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    microservices = tech_sw.get_microservices(dfd)

    # Download docker-compose file
    if not docker_compose_content:
        raw_files = fi.get_file_as_yaml("docker-compose.yml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_yaml("docker-compose.yaml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_yaml("docker-compose*")
        if len(raw_files) == 0:
            return information_flows
        docker_compose_content = raw_files[0]["content"]

    information_flows = dcm_parser.extract_information_flows(docker_compose_content, microservices, information_flows)

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))
    return information_flows


def get_environment_variables(docker_compose_file_URL: str) -> set:
    environment_variables = set()
    try:
        env_files = fi.get_file_as_lines(".env")
        for env in env_files.keys():
            e = env_files[env]
            env_file_content = e["content"].decode('UTF-8')
        env_file_lines = env_file_content.split("\n")
        for line in env_file_lines:
            try:
                environment_variables.add((line.split("=")[0].strip(), line.split("=")[1].strip()))
            except:
                logger.write_log_message("error splitting line in dco_entry.set_microservices", "debug")
    except:
        logger.write_log_message("No .env file exists", "info")
    return environment_variables


def check_image(image: str):
    """Check image for some specific technologies.
    """

    tuple = False
    if "weaveworks/scope" in image:
        tuple = [["monitoring_dashboard"], [("Monitoring Dashboard", "Weave Scope")]]

    return tuple


def detect_microservice(file_path: str, dfd) -> str:
    """Detects, which service a file belongs to based on image given in docker-compose file and dockerfile belonging to file given as input.
    """

    microservices = tech_sw.get_microservices(dfd)
    microservice = False
    dockerfile_path = False

    repo_path = tmp.tmp_config["Repository"]["path"]

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    # Find corresponding dockerfile
    dirs = list()
    found_docker = False

    path = ("/").join(file_path.split("/")[:-1])
    while not found_docker and path != "":
        dirs.append(os.scandir(local_repo_path + "/" + path))
        while dirs:
            dir = dirs.pop()
            for entry in dir:
                if entry.is_file():
                    if entry.name.casefold() == "dockerfile":
                        dockerfile_path = entry.path.split(repo_path.split("/")[1])[1].strip("/")
                        found_docker = True
        path = ("/").join(path.split("/")[:-1])

    if dockerfile_path:
        dockerfile_location = ("/").join(dockerfile_path.split("/")[:-1])

    # find docker-compose path
    try:
        raw_files = fi.get_file_as_lines("docker-compose.yml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_lines("docker-compose.yaml")
        if len(raw_files) == 0:
            raw_files = fi.get_file_as_yaml("docker-compose*")
        if len(raw_files) == 0:
            return microservice
        docker_compose_path = raw_files[0]["path"]          # path in the repo (w/0 "analysed_...")
        docker_compose_location = ("/").join(docker_compose_path.split("/")[:-1])
    except:
        pass

    # path of dockerfile relative to docker-compose file
    # if dockerfile is in same branch in file structure as docker-compose-file:
    try:
        docker_image = dockerfile_location.replace(docker_compose_location, "").strip("/")
    except:
        pass

    # go through microservices to see if dockerfile_image fits an image
    try:
        for m in microservices.keys():
            if microservices[m]["image"] == docker_image:
                microservice = microservices[m]["servicename"]
    except:
        pass

    return microservice
