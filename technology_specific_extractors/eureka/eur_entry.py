import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_eureka(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects Eureka servers if there are any.
    """

    # Server (/microservice classification)
    results = fi.search_keywords("@EnableEurekaServer")

    eureka_server = False
    for r in results.keys():
        eureka_server = tech_sw.detect_microservice(results[r]["path"], dfd)

        for m in microservices.keys():
            if microservices[m]["servicename"] == eureka_server:        # this is the eureka server
                try:
                    microservices[m]["stereotype_instances"].append("service_discovery")
                except:
                    microservices[m]["stereotype_instances"] = "service_discovery"
                try:
                    microservices[m]["tagged_values"].append(("Service Discovery", "Eureka"))
                except:
                    microservices[m]["tagged_values"] = ("Service Discovery", "Eureka")

                # Traceability
                trace = dict()
                trace["parent_item"] = eureka_server
                trace["item"] = "service_discovery"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

    # Clients (/adding info flows) via annotations
    if eureka_server:
        result_paths = set()
        keywords = ["EnableEurekaClient", "EnableDiscoveryClient", "spring-cloud-starter-netflix-eureka-client"]
        for k in keywords:
            results = fi.search_keywords(k)
            for r in results.keys():
                result_paths.add((results[r]["path"], results[r]["line_nr"], results[r]["span"]))

        if not information_flows:
            information_flows = dict()

        participants = set()
        for result_path in result_paths:
            service = tech_sw.detect_microservice(result_path[0], dfd)
            for m in microservices.keys():
                if microservices[m]["servicename"] == service:
                    participants.add((microservices[m]["servicename"], result_path[0], result_path[1], result_path[2]))

        for m in microservices.keys():
            for prop in microservices[m]["properties"]:
                if prop[0] == "eureka_connected" and microservices[m]["servicename"] not in participants:
                    participants.add((microservices[m]["servicename"], prop[2][0], prop[2][1], prop[2][2]))

        for participant in participants:
            if not participant[0] == eureka_server:
                try:
                    id = max(information_flows.keys()) + 1
                except:
                    id = 0
                information_flows[id] = dict()
                information_flows[id]["sender"] = participant[0]
                information_flows[id]["receiver"] = eureka_server
                information_flows[id]["stereotype_instances"] = ["restful_http"]

                trace = dict()
                trace["item"] = participant[0] + " -> " + eureka_server
                trace["file"] = participant[1]
                trace["line"] = participant[2]
                trace["span"] = participant[3]

                traceability.add_trace(trace)

    return microservices, information_flows


def is_eureka(microservice: tuple) -> bool:
    """Checks if a microservice is a Eureka server.
    Input tuple: (servicename, image, type)
    """

    files = fi.search_keywords("@EnableEurekaServer")
    for file in files.keys():
        f = files[file]
        if microservice["pom_path"] in f["path"]:
            return True

    return False


def detect_eureka_server_only(microservices: dict, dfd):

    results = fi.search_keywords("@EnableEurekaServer")
    eureka_servers = set()
    for r in results.keys():
        eureka_servers.add(tech_sw.detect_microservice(results[r]["path"], dfd))

    for e in eureka_servers:
        for m in microservices.keys():
            if microservices[m]["servicename"] == e:        # this is the eureka server
                try:
                    microservices[m]["stereotype_instances"].append("service_discovery")
                except:
                    microservices[m]["stereotype_instances"] = "service_discovery"
                try:
                    microservices[m]["tagged_values"].append(("Service Discovery", "Eureka"))
                except:
                    microservices[m]["tagged_values"] = ("Service Discovery", "Eureka")

    return microservices
