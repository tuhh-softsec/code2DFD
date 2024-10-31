import output_generators.traceability as traceability


def detect_kibana(dfd):
    """Detects logstash services.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

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
            trace["parent_item"] = microservices[m]["name"]
            trace["item"] = "monitoring_dashboard"
            trace["file"] = "heuristic, based on image"
            trace["line"] = "heuristic, based on image"
            trace["span"] = "heuristic, based on image"
            traceability.add_trace(trace)

    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows
