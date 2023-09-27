import core.external_components as ext
import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def detect_zuul(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Detects Zuul gateway if there is one.
    """

    # Server (/microservice classification)
    results = fi.search_keywords("@EnableZuulServer")
    new_results = fi.search_keywords("@EnableZuulProxy")

    for r in new_results.keys():
        try:
            id = max(results.keys()) + 1
        except:
            id = 0
        results[id] = dict()
        results[id] = new_results[r]
    zuul_server = str()
    for r in results.keys():
        zuul_server = tech_sw.detect_microservice(results[r]["path"], dfd)
        for m in microservices.keys():
            if microservices[m]["servicename"] == zuul_server:    # this is the Zuul server
                try:
                    microservices[m]["stereotype_instances"] += ["gateway", "load_balancer"]
                except:
                    microservices[m]["stereotype_instances"] = ["gateway", "load_balancer"]
                try:
                    microservices[m]["tagged_values"] += [("Gateway", "Zuul"), ("Load Balancer", "Ribbon")]
                except:
                    microservices[m]["tagged_values"] = [("Gateway", "Zuul"), ("Load Balancer", "Ribbon")]

                # Traceability
                trace = dict()
                trace["parent_item"] = zuul_server
                trace["item"] = "gateway"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

                # Reverting direction of flow to service discovery, if found
                discovery_server = False
                for m2 in microservices.keys():
                    for s in microservices[m2]["stereotype_instances"]:
                        if s == "service_discovery":
                            discovery_server = microservices[m2]["servicename"]
                            break
                if discovery_server:
                    traceability.revert_flow(zuul_server, discovery_server)
                    for i in information_flows.keys():
                        if information_flows[i]["sender"] == zuul_server and information_flows[i]["receiver"] == discovery_server:
                            information_flows[i]["sender"] = discovery_server
                            information_flows[i]["receiver"] = zuul_server

                # Adding user
                external_components = ext.add_user(external_components)

                # Adding connection user to gateway
                information_flows = ext.add_user_connections(information_flows, zuul_server)

                # Adding flows to other services if routes are in config
                load_balancer = False
                circuit_breaker = False
                for prop in microservices[m]["properties"]:
                    if prop[0] == "load_balancer":
                        load_balancer = prop[1]
                    elif prop[0] == "circuit_breaker":
                        circuit_breaker = prop[1]
                for prop in microservices[m]["properties"]:
                    if prop[0] == "zuul_route" or prop[0] == "zuul_route_serviceId" or prop[0] == "zuul_route_url":
                        receiver = False
                        if prop[0] == "zuul_route" or prop[0] == "zuul_route_serviceId":
                            for m in microservices.keys():
                                for part in prop[1].split("/"):
                                    if microservices[m]["servicename"] in part.casefold():
                                        receiver = microservices[m]["servicename"]
                        else:
                            for m in microservices.keys():
                                for part in prop[1].split("://"):
                                    if microservices[m]["servicename"] in part.split(":")[0].casefold():
                                        receiver = microservices[m]["servicename"]
                        if receiver:
                            try:
                                id = max(information_flows.keys()) + 1
                            except:
                                id = 0
                            information_flows[id] = dict()
                            information_flows[id]["sender"] = zuul_server
                            information_flows[id]["receiver"] = receiver
                            information_flows[id]["stereotype_instances"] = ["restful_http"]

                            trace = dict()
                            trace["item"] = zuul_server + " -> " + receiver
                            trace["file"] = prop[2][0]
                            trace["line"] = prop[2][1]
                            trace["span"] = prop[2][2]
                            traceability.add_trace(trace)

                            if circuit_breaker:
                                information_flows[id]["stereotype_instances"].append("circuit_breaker_link")
                                information_flows[id]["tagged_values"] = [("Circuit Breaker", circuit_breaker)]
                            if load_balancer:
                                information_flows[id]["stereotype_instances"].append("load_balanced_link")
                                try:
                                    information_flows[id]["tagged_values"].append(("Load Balancer", load_balancer))
                                except:
                                    information_flows[id]["tagged_values"] = [("Load Balancer", load_balancer)]

    tmp.tmp_config.set("DFD", "external_components", str(external_components))
    return microservices, information_flows, external_components
