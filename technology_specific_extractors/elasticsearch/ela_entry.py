import output_generators.traceability as traceability


def detect_elasticsearch(dfd):
    """Detects elasticsearch services.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    elasticsearch = False
    for m in microservices.keys():
        if "elasticsearch:" in microservices[m]["image"]:
            elasticsearch = microservices[m]["name"]
            if "stereotype_instances" in microservices[m]:
                microservices[m]["stereotype_instances"].append("search_engine")
            else:
                microservices[m]["stereotype_instances"] = ["search_engine"]
            if "tagged_values" in microservices[m]:
                microservices[m]["tagged_values"].append(("Search Engine", "Elasticsearch"))
            else:
                microservices[m]["tagged_values"] = [("Search Engine", "Elasticsearch")]

    if elasticsearch:
        kibana = False
        for m in microservices.keys():
            if ("Monitoring Dashboard", "Kibana") in microservices[m]["tagged_values"]:
                kibana = microservices[m]["name"]

        if kibana:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = elasticsearch
            information_flows[id]["receiver"] = kibana
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            trace = dict()
            trace["item"] = elasticsearch + " -> " + kibana
            trace["file"] = "implicit"
            trace["line"] = "implicit"
            trace["span"] = "implicit"

            traceability.add_trace(trace)

            # check for faulty flows in other direction
            purge = set()
            for i in information_flows.keys():
                if information_flows[i]["sender"] == kibana and information_flows[i]["receiver"] == elasticsearch:
                    purge.add(i)
            if purge:
                for p in purge:
                    information_flows.pop(p)


    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows
