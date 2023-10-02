import output_generators.traceability as traceability

def detect_kibana(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects logstash services.
    """

    for m in microservices.keys():
        if "kibana:" in microservices[m]["image"]:
            try:
                microservices[m]["stereotype_instances"].append("monitoring_dashboard")
            except:
                microservices[m]["stereotype_instances"] = ["monitoring_dashboard"]
            try:
                microservices[m]["tagged_values"].append(("Monitoring Dashboard", "Kibana"))
            except:
                microservices[m]["tagged_values"] = [("Monitoring Dashboard", "Kibana")]
            trace = dict()
            trace["parent_item"] = microservices[m]["servicename"]
            trace["item"] = "monitoring_dashboard"
            trace["file"] = "heuristic, based on image"
            trace["line"] = "heuristic, based on image"
            trace["span"] = "heuristic, based on image"
            traceability.add_trace(trace)

    return microservices, information_flows
