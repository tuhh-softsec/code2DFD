import output_generators.traceability as traceability


def detect_consul(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects Consul server and clients (service discover, monitoring, configuration).
    """

    # Server
    consul_server = set()
    for m in microservices.keys():
        if "consul:" in microservices[m]["image"]:
            consul_server.add(microservices[m]["servicename"])
            try:
                microservices[m]["stereotype_instances"].append("service_discovery")
            except:
                microservices[m]["stereotype_instances"] = ["service_discovery"]
            try:
                microservices[m]["tagged_values"].append(("Service Discovery", "Consul"))
            except:
                microservices[m]["tagged_values"] = [("Service Discovery", "Consul")]

    # Flows
    if consul_server:
        for m in microservices.keys():
            for prop in microservices[m]["properties"]:
                if prop[0] == "consul_server":
                    for consul in consul_server:
                        if consul == prop[1]:
                            try:
                                id = max(information_flows.keys()) + 1
                            except:
                                id = 0
                            information_flows[id] = dict()
                            information_flows[id]["sender"] = consul
                            information_flows[id]["receiver"] = microservices[m]["servicename"]
                            information_flows[id]["stereotype_instances"] = ["restful_http"]

                            trace = dict()
                            trace["item"] = consul + " -> " + microservices[m]["servicename"]
                            trace["file"] = prop[2][0]
                            trace["line"] = prop[2][1]
                            trace["span"] = prop[2][2]

                            traceability.add_trace(trace)

    return microservices, information_flows
