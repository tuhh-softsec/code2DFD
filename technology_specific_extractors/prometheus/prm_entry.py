import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def detect_prometheus_server(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects prometheus server and adds information flows.
    """

    microservices, information_flows = detect_server_docker(microservices, information_flows, dfd)

    return microservices, information_flows


def detect_server_docker(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects prometheus servers via dockerfiles.
    """

    prometheus_server = str()
    results = fi.search_keywords("prom/prometheus")

    for r in results.keys():
        found = False
        prometheus_server = tech_sw.detect_microservice(results[r]["path"], dfd) # check if any of the builds correspond to this path. If yes, that's the service

        for m in microservices.keys():
            if microservices[m]["servicename"] == prometheus_server:
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("metrics_server")
                else:
                    microservices[m]["stereotype_instances"] = ["metrics_server"]
                if "tagged_values" in microservices[m]:
                    microservices[m]["tagged_values"].append(("Metrics Server", "Prometheus"))
                else:
                    microservices[m]["tagged_values"] = [("Metrics Server", "Prometheus")]
                found = True
        if not found:
            prometheus_server = "prometheus_server"
            # add service
            try:
                id = max(microservices.keys()) + 1
            except:
                id = 0
            microservices[id] = dict()
            microservices[id]["servicename"] = "prometheus_server"
            microservices[id]["image"] = results[r]["path"]
            microservices[id]["stereotype_instances"] = ["metrics_server"]
            microservices[id]["tagged_values"] = [("Metrics Server", "Prometheus")]

        information_flows = detect_connections(microservices, information_flows, results[r], prometheus_server)

    return microservices, information_flows


def detect_connections(microservices: dict, information_flows: dict, dockerfile, prometheus_server: str) -> dict:
    """Parses config file to find connections to prometheus.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]

    for line in dockerfile["content"]:
        if "ADD" in line:
            ini_file_path = line.split(" ")[1]

            ini_file_path = "./analysed_repositories/" + repo_path.split("/")[1] + "/" + ("/").join(dockerfile["path"].split("/")[:-1]) + "/" + ini_file_path

            with open(ini_file_path, "r") as file:
                ini_file = list()
                for line in file.readlines():
                    ini_file.append(line.strip("\n"))

            line_nr = 0
            for line in ini_file:
                target_service = False

                if "targets" in line:
                    if "localhost" in line:
                        parts = line.split(":")
                        for part in parts:
                            part = part.strip().strip("[]\'\" ")
                            for m in microservices.keys():
                                try:
                                    for prop in microservices[m]["tagged_values"]:
                                        if prop[0] == "Port":
                                            if str(prop[1]) == str(part):
                                                target_service = microservices[m]["servicename"]
                                except:
                                    print("failed tagged_values for" + microservices[m]["servicename"])
                    else:
                        parts = line.split(":")
                        for part in parts:
                            part = part.strip().strip("[]\'\" ")
                            for m in microservices.keys():
                                if microservices[m]["servicename"] == part:
                                    target_service = microservices[m]["servicename"]
                if target_service:
                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()
                    information_flows[id]["sender"] = target_service
                    information_flows[id]["receiver"] = prometheus_server
                    information_flows[id]["stereotype_instances"] = ["restful_http"]

                    trace = dict()
                    trace["item"] = target_service + " -> " + prometheus_server
                    trace["file"] = dockerfile["path"]
                    trace["line"] = line_nr
                    trace["span"] = "span"
                    traceability.add_trace(trace)

                line_nr += 1

    return information_flows
