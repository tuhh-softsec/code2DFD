import ast
import os

import yaml

import core.file_interaction as fi
from output_generators.logger import logger
import core.technology_switch as tech_sw
import core.config as tmp
import output_generators.traceability as traceability


def set_information_flows(dfd) -> dict:
    """Adds connections based on parsed config files.
    """

    if tmp.code2dfd_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.code2dfd_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    microservices = tech_sw.get_microservices(dfd)

    # Weavescope
    new_information_flows = weavescope(microservices)
    # merge old and new flows
    for ni in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = new_information_flows[ni]

    # Zuul
    new_information_flows = zuul(microservices)
    for ni in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = new_information_flows[ni]

    tmp.code2dfd_config.set("DFD", "information_flows", str(information_flows).replace("%", "%%"))
    return information_flows


def weavescope(microservices):

    new_information_flows = dict()
    if microservices != None:
        for m in microservices.keys():
            if ("Monitoring Dashboard", "Weave Scope") in microservices[m]["tagged_values"]:
                for mi in microservices.keys():
                    if not microservices[mi]["name"] == microservices[m]["name"]:
                        try:
                            id = max(new_information_flows.keys()) + 1
                        except:
                            id = 0
                        new_information_flows[id] = dict()

                        new_information_flows[id]["sender"] = microservices[mi]["name"]
                        new_information_flows[id]["receiver"] = microservices[m]["name"]
                        new_information_flows[id]["stereotype_instances"] = ["restful_http"]

                        trace = dict()
                        trace["item"] = microservices[mi]["name"] + " -> " + microservices[m]["name"]
                        trace["file"] = "implicit for weavescope"
                        trace["line"] = "implicit for weavescope"
                        trace["span"] = "implicit for weavescope"

                        traceability.add_trace(trace)

    return new_information_flows


def zuul(microservices):
    new_information_flows = dict()
    for m in microservices.values():
        if ("Gateway", "Zuul") in m["tagged_values"]:
            try:
                path = os.path.dirname(m["pom_path"])
            except:
                break

            contents = fi.get_repo_contents_local(path)
            while contents:
                c = contents.pop()
                path = c[1]
                if os.path.isdir(c):
                    contents.update(fi.get_repo_contents_local(path))
                else:
                    filename = os.path.basename(path)
                    if filename == "application.properties":
                        logger.info("Found application.properties here: " + str(path))
                        new_information_flows = extract_routes_properties(c.path, microservices[m]["servicename"])
                    elif filename == "application.yaml" or filename == "application.yml" or filename == "bootstrap.yml" or filename == "bootstrap.yaml":
                        logger.info("Found properteis file here: " + str(path))
                        new_information_flows = extract_routes_yaml(path, microservices[m]["servicename"])

    return new_information_flows


def extract_routes_properties(path, service):
    try:
        file = fi.file_as_lines(path)
        for line in file:
            if "spring.application.name" in line:
                microservice = str()
                if "=" in line:
                    microservice = line.split("=")[1].strip()
                new_information_flows = dict()
                if microservice:
                    try:
                        id = max(new_information_flows.keys()) + 1
                    except:
                        id = 0
                    new_information_flows[id] = dict()

                    new_information_flows[id]["sender"] = service
                    new_information_flows[id]["receiver"] = microservice
                    new_information_flows[id]["stereotype_instances"] = ["restful_http"]
            return new_information_flows
    except:
        return False
    return


def extract_routes_yaml(path, service):
    try:
        with open(path, 'r') as f:
            text = f.read()
        for document in yaml.load(text, Loader=yaml.FullLoader):
            routes = document.get("zuul").get("routes")

            new_information_flows = dict()
            try:
                id = max(new_information_flows.keys()) + 1
            except:
                id = 0
            new_information_flows[id] = dict()

            new_information_flows[id]["sender"] = service
            new_information_flows[id]["receiver"] = str(routes)
            new_information_flows[id]["stereotype_instances"] = ["restful_http"]
            return new_information_flows
    except:
        return False
