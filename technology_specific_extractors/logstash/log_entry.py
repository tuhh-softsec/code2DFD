import output_generators.traceability as traceability


def detect_logstash(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Detects logstash services.
    """

    # Service
    logstash = False
    trace_info = False
    for m in microservices.keys():
        if "logstash:" in microservices[m]["image"]:
            logstash = microservices[m]["servicename"]
            try:
                microservices[m]["stereotype_instances"].append("logging_server")
            except:
                microservices[m]["stereotype_instances"] = ["logging_server"]
            try:
                microservices[m]["tagged_values"].append(("Logging Server", "Logstash"))
            except:
                microservices[m]["tagged_values"] = [("Logging Server", "Logstash")]

    if not logstash:
        for m in microservices.keys():
            if "properties" in microservices[m]:
                for prop in microservices[m]["properties"]:
                    if prop[0] == "logstash_server":
                        trace_info = dict()
                        trace_info[0] = prop[2][0]
                        trace_info[1] = prop[2][1]
                        trace_info[2] = prop[2][2]

                        logstash_server = prop[1].strip().strip("-").strip()
                        if ":" in logstash_server:
                            # internal via name
                            logstash_host = logstash_server.split(":")[0]
                            for mi in microservices.keys():
                                if logstash_host == microservices[mi]["servicename"]:
                                    logstash = microservices[mi]["servicename"]
                                    if "stereotype_instances" in microservices[mi]:
                                        microservices[mi]["stereotype_instances"].append("logging_server")
                                    else:
                                        microservices[mi]["stereotype_instances"] = ["logging_server"]
                                    if "tagged_values" in microservices[mi]:
                                        microservices[mi]["tagged_values"].append(("Logging Server", "Logstash"))
                                    else:
                                        microservices[mi]["tagged_values"] = [("Logging Server", "Logstash")]

                            # internal via port
                            if not logstash:
                                logstash_port = int(logstash_server.split(":")[1].strip().strip(""))
                                for mi in microservices.keys():
                                    for prop2 in microservices[mi]["properties"]:
                                        if prop2[0] == "Port" and int(prop2[1]) == logstash_port:
                                            logstash = microservices[mi]["servicename"]
                                            if "stereotype_instances" in microservices[mi]:
                                                microservices[mi]["stereotype_instances"].append("logging_server")
                                            else:
                                                microservices[mi]["stereotype_instances"] = ["logging_server"]
                                            if "tagged_values" in microservices[mi]:
                                                microservices[mi]["tagged_values"].append(("Logging Server", "Logstash"))
                                            else:
                                                microservices[mi]["tagged_values"] = [("Logging Server", "Logstash")]

                            # external
                            if not logstash:
                                logstash_port = int(logstash_server.split(":")[1].strip().strip(""))
                                try:
                                    id = max(external_components.keys()) + 1
                                except:
                                    id = 0
                                external_components[id] = dict()
                                external_components[id]["name"] = "logstash"
                                external_components[id]["type"] = "external_component"
                                external_components[id]["stereotype_instances"] = ["logging_server", "exitpoint"]
                                external_components[id]["tagged_values"] = [("Logging Server", "Logstash"), ("Port", logstash_port)]

                                trace = dict()
                                trace["item"] = "logstash"
                                trace["file"] = trace_info[0]
                                trace["line"] = trace_info[1]
                                trace["span"] = trace_info[2]
                                traceability.add_trace(trace)

                                try:
                                    id = max(information_flows.keys()) + 1
                                except:
                                    id = 0
                                information_flows[id] = dict()
                                information_flows[id]["sender"] = microservices[m]["servicename"]
                                information_flows[id]["receiver"] = "logstash"
                                information_flows[id]["stereotype_instances"] = ["restful_http"]

                                trace = dict()
                                trace["item"] = microservices[m]["servicename"] + " -> " + "logstash"
                                trace["file"] = trace_info[0]
                                trace["line"] = trace_info[1]
                                trace["span"] = trace_info[2]

                                traceability.add_trace(trace)



        # Flow to elasticsearch
    if logstash:
        if trace_info:
            trace = dict()
            trace["item"] = logstash
            trace["file"] = trace_info[0]
            trace["line"] = trace_info[1]
            trace["span"] = trace_info[2]
            traceability.add_trace(trace)

        elasticsearch = False
        for m in microservices.keys():
            if ("Search Engine", "Elasticsearch") in microservices[m]["tagged_values"]:
                elasticsearch = microservices[m]["servicename"]
        if elasticsearch:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = logstash
            information_flows[id]["receiver"] = elasticsearch
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            trace = dict()
            trace["item"] = logstash + " -> " + elasticsearch
            trace["file"] = "implicit"
            trace["line"] = "implicit"
            trace["span"] = "implicit"

            traceability.add_trace(trace)

        # Flow from services
        for m in microservices.keys():
            for prop in microservices[m]["properties"]:
                if prop[0] == "logstash_server":
                    if logstash in prop[1]:
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = microservices[m]["servicename"]
                        information_flows[id]["receiver"] = logstash
                        information_flows[id]["stereotype_instances"] = ["restful_http"]

                        trace = dict()
                        trace["item"] = microservices[m]["servicename"] + " -> " + logstash
                        trace["file"] = prop[2][0]
                        trace["line"] = prop[2][1]
                        trace["span"] = prop[2][2]

                        traceability.add_trace(trace)

    return microservices, information_flows, external_components
