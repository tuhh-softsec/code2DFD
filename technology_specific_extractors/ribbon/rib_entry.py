import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_ribbon_load_balancers(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects load balancing via Ribbon.
    """

    microservices = detect_client_side(microservices, dfd)

    return microservices, information_flows


def detect_client_side(microservices: dict, dfd) -> dict:
    """Detects client side load balncing.
    """

    results = fi.search_keywords("RibbonClient")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@RibbonClient" in line:
                for m in microservices.keys():
                    if microservices[m]["servicename"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("load_balancer")
                        except:
                            microservices[m]["stereotype_instances"] = ["load_balancer"]
                        try:
                            microservices[m]["tagged_values"].append(("Load Balancer", "Ribbon"))
                        except:
                            microservices[m]["tagged_values"] = [("Load Balancer", "Ribbon")]

    return microservices
