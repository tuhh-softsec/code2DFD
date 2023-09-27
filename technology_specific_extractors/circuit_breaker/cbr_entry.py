import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_circuit_breakers(microservices: dict, information_flows: dict, dfd) -> dict:
    """Find circuit breakers.
    """

    results = fi.search_keywords("@EnableCircuitBreaker")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        # Check if circuit breaker tech was found
        circuit_breaker_tuple = False
        correct_id = False
        for m in microservices.keys():
            if microservices[m]["servicename"] == microservice:
                correct_id = m
                for prop in microservices[m]["properties"]:
                    if prop[0] == "circuit_breaker":
                        circuit_breaker_tuple = ("Circuit Breaker", prop[1])

        if correct_id:
            for line_nr in range(len(results[r]["content"])):
                line = results[r]["content"][line_nr]
                if "@EnableCircuitBreaker" in line:
                    if "stereotype_instances" in microservices[correct_id]:
                        microservices[correct_id]["stereotype_instances"].append("circuit_breaker")
                    else:
                        microservices[correct_id]["stereotype_instances"] = ["circuit_breaker"]

                    if circuit_breaker_tuple:
                        if "tagged_values" in microservices[correct_id]:
                            microservices[correct_id]["tagged_values"].append(circuit_breaker_tuple)
                        else:
                            microservices[correct_id]["tagged_values"] = [circuit_breaker_tuple]

                    # adjust flows going from this service
                    for i in information_flows.keys():
                        if information_flows[i]["sender"] == microservice:
                            if "stereotype_instances" in information_flows[i]:
                                information_flows[i]["stereotype_instances"].append("circuit_breaker_link")
                            else:
                                information_flows[i]["stereotype_instances"] = ["circuit_breaker_link"]
                            if circuit_breaker_tuple:
                                if "tagged_values" in information_flows[i]:
                                    if type(information_flows[i]["tagged_values"]) == list:
                                        information_flows[i]["tagged_values"].append(circuit_breaker_tuple)
                                    else:
                                        information_flows[i]["tagged_values"].add(circuit_breaker_tuple)
                                else:
                                    information_flows[i]["tagged_values"] = [circuit_breaker_tuple]

    return microservices, information_flows


def detect_circuit_breaker_tech(path):

    circuit_breaker_tuple = False

    return circuit_breaker_tuple
