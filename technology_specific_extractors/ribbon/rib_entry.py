import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_ribbon_load_balancers(dfd):
    """Detects load balancing via Ribbon.
    """

    microservices = dfd["microservices"]

    microservices = detect_client_side(microservices, dfd)

    dfd["microservices"] = microservices


def detect_client_side(microservices: dict, dfd) -> dict:
    """Detects client side load balncing.
    """

    results = fi.search_keywords("RibbonClient")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@RibbonClient" in line:
                for m in microservices.keys():
                    if microservices[m]["name"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("load_balancer")
                        except:
                            microservices[m]["stereotype_instances"] = ["load_balancer"]
                        try:
                            microservices[m]["tagged_values"].append(("Load Balancer", "Ribbon"))
                        except:
                            microservices[m]["tagged_values"] = [("Load Balancer", "Ribbon")]

    return microservices
