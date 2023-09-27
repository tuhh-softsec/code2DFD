import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_spring_admin_server(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects Spring Admin Servers.
    """

    results = fi.search_keywords("@EnableAdminServer")
    admin_server = False
    for r in results.keys():
        admin_server = tech_sw.detect_microservice(results[r]["path"], dfd)
        for m in microservices.keys():
            if microservices[m]["servicename"] == admin_server:
                try:
                    microservices[m]["stereotype_instances"].append("administration_server")
                except:
                    microservices[m]["stereotype_instances"] = "administration_server"
                try:
                    microservices[m]["tagged_values"].append(("Administration Server", "Spring Boot Admin"))
                except:
                    microservices[m]["tagged_values"] = ("Administration Server", "Spring Boot Admin")
                admin_server = microservices[m]["servicename"]

                # Traceability
                trace = dict()
                trace["parent_item"] = admin_server
                trace["item"] = "administration_server"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)


    for m in microservices.keys():
        host = False
        reverse = False
        config_reverse = False
        for prop in microservices[m]["properties"]:
            if prop[0] == "admin_server_url":
                trace_info = dict()
                trace_info[0] = prop[2][0]
                trace_info[1] = prop[2][1]
                trace_info[2] = prop[2][2]
                if "://" in prop[1]:
                    host = prop[1].split("://")[1].split(":")[0]
        if "stereotype_instances" in microservices[m] and "service_discovery" in microservices[m]["stereotype_instances"]:
            reverse = True
        if "stereotype_instances" in microservices[m] and "configuration_server" in microservices[m]["stereotype_instances"]:
            config_reverse = True
        if host and host == admin_server:
            if reverse: # flow admin -> service-discovery
                found = False
                for i in information_flows.keys():
                    if information_flows[i]["sender"] == admin_server and information_flows[i]["receiver"] == microservices[m]["servicename"]:
                        found = True
                        information_flows[i]["sender"] = microservices[m]["servicename"]
                        information_flows[i]["receiver"] = admin_server

                        trace = dict()
                        trace["item"] = microservices[m]["servicename"] + " -> " + admin_server
                        trace["file"] = trace_info[0]
                        trace["line"] = trace_info[1]
                        trace["span"] = trace_info[2]

                        traceability.add_trace(trace)

                if not found:
                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()

                    information_flows[id]["sender"] = microservices[m]["servicename"]
                    information_flows[id]["receiver"] = admin_server
                    information_flows[id]["stereotype_instances"] = ["restful_http"]

                    trace = dict()
                    trace["item"] = microservices[m]["servicename"] + " -> " + admin_server
                    trace["file"] = trace_info[0]
                    trace["line"] = trace_info[1]
                    trace["span"] = trace_info[2]

                    traceability.add_trace(trace)


            elif config_reverse:
                found = False
                for i in information_flows.keys():
                    if information_flows[i]["sender"] == microservices[m]["servicename"] and information_flows[i]["receiver"] == admin_server:
                        found = True
                        information_flows[i]["sender"] = admin_server
                        information_flows[i]["receiver"] = microservices[m]["servicename"]

                        trace = dict()
                        trace["item"] = admin_server + " -> " + microservices[m]["servicename"]
                        trace["file"] = trace_info[0]
                        trace["line"] = trace_info[1]
                        trace["span"] = trace_info[2]

                        traceability.add_trace(trace)

                if not found:
                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()

                    information_flows[id]["sender"] = admin_server
                    information_flows[id]["receiver"] = microservices[m]["servicename"]
                    information_flows[id]["stereotype_instances"] = ["restful_http"]

                    trace = dict()
                    trace["item"] = admin_server + " -> " + microservices[m]["servicename"]
                    trace["file"] = trace_info[0]
                    trace["line"] = trace_info[1]
                    trace["span"] = trace_info[2]

                    traceability.add_trace(trace)

            else:
                try:
                    id = max(information_flows.keys()) + 1
                except:
                    id = 0

                information_flows[id] = dict()
                information_flows[id]["sender"] = admin_server
                information_flows[id]["receiver"] = microservices[m]["servicename"]
                information_flows[id]["stereotype_instances"] = ["restful_http"]

                trace = dict()
                trace["item"] = admin_server + " -> " + microservices[m]["servicename"]
                trace["file"] = trace_info[0]
                trace["line"] = trace_info[1]
                trace["span"] = trace_info[2]

                traceability.add_trace(trace)


    return microservices, information_flows
