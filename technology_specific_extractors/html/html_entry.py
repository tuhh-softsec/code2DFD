import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def set_information_flows(dfd):
    """Looks for connections between services via html sites / href's.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    results = fi.search_keywords("href")
    for r in results.keys():
        for line in results[r]["content"]:
            if "href" in line:
                try:
                    stereotypes = ["restful_http"]
                    protocol = line.split("=")[0].strip().strip("\"").strip()
                    if protocol.casefold() == "https":
                        stereotypes.append("ssl_enabled")
                    address = line.split("=")[1].split("\"")[1]
                    address_parts = address.split("/")
                    for address_part in address_parts:
                        for m in microservices.keys():
                            if address_part == microservices[m]["name"]:
                                microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
                                if microservice:
                                    try:
                                        id = max(information_flows.keys()) + 1
                                    except:
                                        id = 0
                                    information_flows[id] = dict()

                                    information_flows[id]["sender"] = microservice
                                    information_flows[id]["receiver"] = microservices[m]["name"]
                                    information_flows[id]["stereotype_instances"] = stereotypes

                                    trace = dict()
                                    trace["item"] = microservice + " -> " + microservices[m]["name"]
                                    trace["file"] = results[r]["path"]
                                    trace["line"] = results[r]["line_nr"]
                                    trace["span"] = results[r]["span"]
                                    traceability.add_trace(trace)

                except:
                    pass
    dfd["information_flows"] = information_flows
