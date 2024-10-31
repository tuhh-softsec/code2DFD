import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_grafana(dfd):
    """Detects grafana server and connections.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    grafana_server = str()
    results = fi.search_keywords("grafana/grafana")

    for r in results.keys():
        grafana_server = tech_sw.detect_microservice(results[r]["path"], dfd)
        for m in microservices.keys():
            if microservices[m]["name"] == grafana_server:
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("monitoring_dashboard")
                else:
                    microservices[m]["stereotype_instances"] = ["monitoring_dashboard"]
                if "tagged_values" in microservices[m]:
                    microservices[m]["tagged_values"].append(("Monitoring Dashboard", "Grafana"))
                else:
                    microservices[m]["tagged_values"] = [("Monitoring Dashboard", "Grafana")]

                trace = dict()
                trace["parent_item"] = microservices[m]["name"]
                trace["item"] = "monitoring_dashboard"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]
                traceability.add_trace(trace)

    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows
