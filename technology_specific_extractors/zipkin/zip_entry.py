import output_generators.traceability as traceability


def detect_zipkin_server(dfd: dict, iterative=False):
    """Detects zipkin server and connections to it.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    zipkin_server_exists, connections_exist = False, False

    for m in microservices.keys():
        circuit_breaker, load_balancer = False, False
        tagged_values, load_balancer, circuit_breaker = False, False, False

        for prop2 in microservices[m]["properties"]:
            if prop2[0] == "load_balancer":
                load_balancer = prop2[1]
            elif prop2[0] == "circuit_breaker":
                circuit_breaker = prop2[1]

        if load_balancer:
            load_balancer = True
            try:
                tagged_values.add(("Load Balancer", load_balancer))
            except:
                tagged_values = {("Load Balancer", load_balancer)}

        if circuit_breaker:
            circuit_breaker = True
            try:
                tagged_values.add(("Circuit Breaker", circuit_breaker))
            except:
                tagged_values = {("Circuit Breaker", circuit_breaker)}

        zipkin_server = False
        for prop in microservices[m]["properties"]:
            if prop[0] == "zipkin_url":
                connections_exist = prop[1]
                zipkin_url = prop[1]
                parts = zipkin_url.split("/")
                for m2 in microservices.keys():
                    for part in parts:
                        if part.split(":")[0] == microservices[m2]["name"]:
                            zipkin_server = microservices[m2]["name"]
                        if not zipkin_server:
                            if (":" in part and
                                part.split(":")[1] in [b for (a, b, c) in microservices[m2]["properties"] if (a == "port")]):
                                zipkin_server = microservices[m2]["name"]
                        if zipkin_server:
                            correct_id = m2
                            try:
                                id = max(information_flows.keys()) + 1
                            except:
                                id = 0
                            information_flows[id] = dict()
                            information_flows[id]["sender"] = microservices[m]["name"]
                            information_flows[id]["receiver"] = zipkin_server
                            information_flows[id]["stereotype_instances"] = ["restful_http"]
                            if tagged_values:
                                information_flows[id]["tagged_values"] = tagged_values
                            if circuit_breaker:
                                information_flows[id]["stereotype_instances"].append("circuit_breaker_link")
                            if load_balancer:
                                information_flows[id]["stereotype_instances"].append("load_balanced_link")

                            trace = dict()
                            trace["item"] = microservices[m]["name"] + " -> " + zipkin_server
                            trace["file"] = prop[2][0]
                            trace["line"] = prop[2][1]
                            trace["span"] = prop[2][2]
                            traceability.add_trace(trace)

        if not zipkin_server:
            if "openzipkin/zipkin" in microservices[m]["image"]:
                zipkin_server = microservices[m]["name"]
                correct_id = m

        if zipkin_server:
            zipkin_server_exists = True
            if "stereotype_instances" in microservices[correct_id]:
                microservices[correct_id]["stereotype_instances"].append("tracing_server")
            else:
                microservices[correct_id]["stereotype_instances"] = ["tracing_server"]
            if "tagged_values" in microservices[correct_id]:
                microservices[correct_id]["tagged_values"].append(("Tracing Server", "Zipkin"))
            else:
                microservices[correct_id]["tagged_values"] =[("Tracing Server", "Zipkin")]

    if not zipkin_server_exists and connections_exist:
        if "http:" in connections_exist:
            port = connections_exist.split("http:")[1]
            if ":" in port:
                port = port.split(":")[1].strip("/").strip()
        id_ = max(microservices.keys(), default=-1) + 1
        microservices[id_] = dict()
        microservices[id_]["name"] = "zipkin-server"
        microservices[id_]["image"] = "placeholder_image"
        microservices[id_]["properties"] = [("port", port, ("file", "line", "span"))]
        microservices[id_]["stereotype_instances"] = ["tracing_server"]
        microservices[id_]["tagged_values"] = [("Tracing Server", "Zipkin")]

        dfd["microservices"] = microservices
        dfd["information_flows"] = information_flows
        if not iterative:
            detect_zipkin_server(dfd, True)

    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows
