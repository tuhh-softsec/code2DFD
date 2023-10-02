import os

import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def detect_turbine(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects turbine server.
    """

    microservices = detect_turbine_server(microservices, dfd)
    microservices, information_flows = detect_turbineamqp(microservices, information_flows, dfd)
    microservices, information_flows = detect_turbine_stream(microservices, information_flows, dfd)

    return microservices, information_flows


def detect_turbine_server(microservices: dict, dfd) -> dict:
    """Detects standard turbine servers.
    """

    results = fi.search_keywords("@EnableTurbine")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@EnableTurbine" in line:
                for m in microservices.keys():
                    if microservices[m]["servicename"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("monitoring_server")
                        except:
                            microservices[m]["stereotype_instances"] = ["monitoring_server"]
                        try:
                            microservices[m]["tagged_values"].append(("Monitoring Server", "Turbine"))
                        except:
                            microservices[m]["tagged_values"] = [("Monitoring Server", "Turbine")]

                        trace = dict()
                        trace["parent_item"] = microservices[m]["servicename"]
                        trace["item"] = "monitoring_server"
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]
                        traceability.add_trace(trace)

    return microservices


def detect_turbineamqp(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects turbine servers implementes via EnableTurbineAmqp annotation.
    """

    results = fi.search_keywords("@EnableTurbineAmqp")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@EnableTurbineAmqp" in line:
                for m in microservices.keys():
                    if microservices[m]["servicename"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("monitoring_server")
                        except:
                            microservices[m]["stereotype_instances"] = "monitoring_server"
                        try:
                            microservices[m]["tagged_values"].append(("Monitoring Server", "Turbine"))
                        except:
                            microservices[m]["tagged_values"] = ("Monitoring Server", "Turbine")

                        trace = dict()
                        trace["parent_item"] = microservices[m]["servicename"]
                        trace["item"] = "monitoring_server"
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]
                        traceability.add_trace(trace)

                    if ("Monitoring Dashboard", "Hystrix") in microservices[m]["tagged_values"]:
                        dashboard = microservices[m]["servicename"]
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = microservice
                        information_flows[id]["receiver"] = dashboard
                        information_flows[id]["stereotype_instances"] = ["restful_http"]

                        trace = dict()
                        trace["item"] = microservice + " -> " + dashboard
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]

                        traceability.add_trace(trace)

                    elif ("Message Broker", "RabbitMQ") in microservices[m]["tagged_values"]:
                        rabbitmq = microservices[m]["servicename"]
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = rabbitmq
                        information_flows[id]["receiver"] = microservice
                        information_flows[id]["stereotype_instances"] = ["restful_http"]

                        trace = dict()
                        trace["item"] = rabbitmq + " -> " + microservice
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]

                        traceability.add_trace(trace)

    return microservices, information_flows


def detect_turbine_stream(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects Tubrine servers via EnableTurbineStream annotation.
    """

    uses_rabbit = False
    rabbitmq = False
    turbine_server = False
    results = fi.search_keywords("EnableTurbineStream")     # content, name, path
    for r in results.keys():
        trace_info = (False, False, False)
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@EnableTurbineStream" in line:
                for id in microservices.keys():
                    if microservices[id]["servicename"] == microservice:
                        turbine_server = microservices[id]["servicename"]
                        try:
                            microservices[id]["stereotype_instances"].append("monitoring_server")
                        except:
                            microservices[id]["stereotype_instances"] = "monitoring_server"
                        try:
                            microservices[id]["tagged_values"].append(("Monitoring Server", "Turbine"))
                        except:
                            microservices[id]["tagged_values"] = ("Monitoring Server", "Turbine")

                        trace = dict()
                        trace["parent_item"] = microservices[id]["servicename"]
                        trace["item"] = "monitoring_server"
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]
                        traceability.add_trace(trace)

                        # find pom_file and check which broker there is a dependency for
                        repo_path = tmp.tmp_config["Repository"]["path"]
                        path = results[r]["path"]

                        found_pom = False

                        local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

                        dirs = list()

                        path = ("/").join(path.split("/")[:-1])
                        dirs.append(os.scandir(local_repo_path + "/" + path))

                        while path != "" and not found_pom:
                            dir = dirs.pop()
                            for entry in dir:
                                if entry.is_file():
                                    if entry.name.casefold() == "pom.xml":
                                        with open(entry.path, "r") as file:
                                            lines = file.readlines()
                                        for line in lines:
                                            if "<artifactId>spring-cloud-starter-stream-rabbit</artifactId>" in line:
                                                uses_rabbit = True
                                                trace_info = (results[r]["path"], results[r]["line_nr"], results[r]["span"])
                            path = ("/").join(path.split("/")[:-1])
                            dirs.append(os.scandir(local_repo_path + "/" + path))

                    if ("Monitoring Dashboard", "Hystrix") in microservices[id]["tagged_values"]:
                        dashboard = microservices[id]["servicename"]
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = microservice
                        information_flows[id]["receiver"] = dashboard
                        information_flows[id]["stereotype_instances"] = ["restful_http"]

                        trace = dict()
                        trace["item"] = microservice + " -> " + dashboard
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]

                        traceability.add_trace(trace)

    if turbine_server and uses_rabbit:
        for m in microservices.keys():
            if ("Message Broker", "RabbitMQ") in microservices[m]["tagged_values"]:
                rabbitmq = microservices[m]["servicename"]
                try:
                    id = max(information_flows.keys()) + 1
                except:
                    id = 0
                information_flows[id] = dict()
                information_flows[id]["sender"] = rabbitmq
                information_flows[id]["receiver"] = turbine_server
                information_flows[id]["stereotype_instances"] = ["restful_http"]

                trace = dict()
                trace["item"] = rabbitmq + " -> " + turbine_server
                trace["file"] = trace_info[0]
                trace["line"] = trace_info[1]
                trace["span"] = trace_info[2]

                traceability.add_trace(trace)

                # check if flow in other direction exists (can happen faultely in docker compse)
                for i in information_flows.keys():
                    if information_flows[i]["sender"] == turbine_server and information_flows[i]["receiver"] == rabbitmq:
                        information_flows.pop(i)

    # clients:
    if uses_rabbit and rabbitmq:
        results = fi.search_keywords("spring-cloud-netflix-hystrix-stream")     # content, name, path
        for r in results.keys():
            microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = microservice
            information_flows[id]["receiver"] = rabbitmq
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            trace = dict()
            trace["item"] = microservice + " -> " + rabbitmq
            trace["file"] = trace_info[0]
            trace["line"] = trace_info[1]
            trace["span"] = trace_info[2]

            traceability.add_trace(trace)

    return microservices, information_flows
