import core.external_components as ext
import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_spring_cloud_gateway(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Detetcs Spring Cloud Gateway.
    """

    server = False
    results = fi.search_keywords("spring-cloud-starter-gateway")
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        if microservice:
            for m in microservices.keys():
                if microservices[m]["servicename"] == microservice:
                    server = microservice
                    try:
                        microservices[m]["stereotype_instances"].append("gateway")
                    except:
                        microservices[m]["stereotype_instances"] = "gateway"
                    try:
                        microservices[m]["tagged_values"].append(("Gateway", "Spring Cloud Gateway"))
                    except:
                        microservices[m]["tagged_values"] = ("Gateway", "Spring Cloud Gateway")

                    # Traceability
                    trace = dict()
                    trace["parent_item"] = microservice
                    trace["item"] = "gateway"
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)

    if server:

        # Reverting direction of flow to service discovery, if found
        discovery_server = False
        for m2 in microservices.keys():
            for s in microservices[m2]["stereotype_instances"]:
                if s == "service_discovery":
                    discovery_server = microservices[m2]["servicename"]
                    break
        if discovery_server:
            for i in information_flows.keys():
                if information_flows[i]["sender"] == server and information_flows[i]["receiver"] == discovery_server:
                    information_flows[i]["sender"] = discovery_server
                    information_flows[i]["receiver"] = server

                    traceability.revert_flow(server, discovery_server)

        # Adding user
        external_components = ext.add_user(external_components)

        # Adding connection user to gateway
        information_flows = ext.add_user_connections(information_flows, server)

    # clients
    if server:
        for m in microservices.keys():
            for prop in microservices[m]["properties"]:
                target_service = False
                if prop[0] == "spring_cloud_gateway_route":
                    for m2 in microservices.keys():
                        if microservices[m2]["servicename"] == prop[1]:
                            target_service = prop[1]
                if target_service:
                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()
                    information_flows[id]["sender"] = server
                    information_flows[id]["receiver"] = target_service
                    information_flows[id]["stereotype_instances"] = ["restful_http"]

                    trace = dict()
                    trace["item"] = server + " -> " + target_service
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]
                    traceability.add_trace(trace)

    return microservices, information_flows, external_components
