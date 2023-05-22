

def detect_kibana(microservices: dict, information_flows: dict) -> dict:
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

    return microservices, information_flows
