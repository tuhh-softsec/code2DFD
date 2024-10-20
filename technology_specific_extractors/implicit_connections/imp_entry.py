import ast
import os

import requests
import yaml

import core.file_interaction as fi
from output_generators.logger import logger
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def set_information_flows(dfd) -> dict:
    """Adds connections based on parsed config files.
    """

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
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

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows).replace("%", "%%"))
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
    if microservices != None:
        for m in microservices.keys():
            if ("Gateway", "Zuul") in microservices[m]["tagged_values"]:
                repo_path = tmp.tmp_config["Repository"]["path"]

                repo = fi.get_repo(repo_path)
                try:
                    path = os.path.dirname(microservices[m]["pom_path"])
                except:
                    break

                contents = repo.get_contents(path)
                if type(contents) != list:
                    contents = [contents]
                while contents:
                    c = contents.pop()
                    if c.type == "dir":
                        contents.extend(repo.get_contents(c.path))
                    else:
                        filename = os.path.basename(c.path)
                        if filename == "application.properties":
                            logger.info("Found application.properties here: " + str(c.path))
                            file_url = c.download_url
                            new_information_flows = extract_routes_properties(file_url, microservices[m]["name"])
                        elif filename == "application.yaml" or filename == "application.yml" or filename == "bootstrap.yml" or filename == "bootstrap.yaml":
                            logger.info("Found properteis file here: " + str(c.path))
                            file_url = c.download_url
                            new_information_flows = extract_routes_yaml(file_url, microservices[m]["name"])

    return new_information_flows


def extract_routes_properties(url, service):
    try:
        file = fi.file_as_lines(url)
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


def extract_routes_yaml(url, service):
    try:
        raw_file = requests.get(url)
        for document in yaml.load_all(raw_file.text, Loader = yaml.FullLoader):
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
