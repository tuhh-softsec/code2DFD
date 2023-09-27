import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_load_balancers(microservices: dict, information_flows: dict, dfd) -> dict:
    """Find load balancers.
    """

    results = fi.search_keywords("@LoadBalanced")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)

        correct_id = False
        for m in microservices.keys():
            if microservices[m]["servicename"] == microservice:
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("load_balancer")
                else:
                    microservices[m]["stereotype_instances"] = ["load_balancer"]
                if "tagged_values" in microservices[correct_id]:
                    microservices[m]["tagged_values"].append(('Load Balancer', "Spring Cloud"))
                else:
                    microservices[m]["tagged_values"] = [('Load Balancer', "Spring Cloud")]

                # # Traceability
                trace = dict()

                trace["parent_item"] = microservice
                trace["item"] = "load_balancer"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

                # adjust flows going from this service
                for i in information_flows.keys():
                    if information_flows[i]["sender"] == microservice:
                        if "stereotype_instances" in information_flows[i]:
                            information_flows[i]["stereotype_instances"].append("load_balanced_link")
                        else:
                            information_flows[i]["stereotype_instances"] = ["load_balanced_link"]

                        if "tagged_values" in information_flows[i]:
                            if type(information_flows[i]["tagged_values"]) == list:
                                information_flows[i]["tagged_values"].append(('Load Balancer', "Spring Cloud"))
                            else:
                                information_flows[i]["tagged_values"].add(('Load Balancer', "Spring Cloud"))
                        else:
                            information_flows[i]["tagged_values"] = [('Load Balancer', "Spring Cloud")]

    return microservices, information_flows
