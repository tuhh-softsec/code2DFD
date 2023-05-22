import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_grafana(microservices: dict, information_flows: dict) -> dict:
    """Detects grafana server and connections.
    """

    grafana_server = str()
    results = fi.search_keywords("grafana/grafana")

    for r in results.keys():
        grafana_server = tech_sw.detect_microservice(results[r]["path"])
        for m in microservices.keys():
            if microservices[m]["servicename"] == grafana_server:
                microservices[m]["type"] = "infrastructural_service"
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("monitoring_dashboard")
                else:
                    microservices[m]["stereotype_instances"] = ["monitoring_dashboard"]
                if "tagged_values" in microservices[m]:
                    microservices[m]["tagged_values"].append(("Monitoring Dashboard", "Grafana"))
                else:
                    microservices[m]["tagged_values"] = [("Monitoring Dashboard", "Grafana")]

    return microservices, information_flows
