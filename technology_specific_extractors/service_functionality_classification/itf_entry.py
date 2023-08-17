import output_generators.traceability as traceability

def classify_internal_infrastructural(microservices: dict) -> dict:
    """Classifies processes as either internal or infrastructural.
    The latter if they are marked as one of the known infrastructural technologies.
    """

    infrastructural_stereotypes = [ "configuration_server",
                                    "administration_server",
                                    "service_discovery",
                                    "gateway",
                                    "message_broker",
                                    "authentication_server",
                                    "authorization_server",
                                    "logging_server",
                                    "monitoring_server",
                                    "monitoring_dashboard",
                                    "web_server",
                                    "web_application",
                                    "deployment_server",
                                    "stream_aggregator",
                                    "tracing_server",
                                    "metrics_server",
                                    "visualization",
                                    "search_engine",
                                    "proxy"
                                    ]

    for m in microservices.keys():
        infrastructural = False
        if not "database" in microservices[m]["stereotype_instances"]:
            deciding_stereotype = None
            for s in microservices[m]["stereotype_instances"]:
                if s in infrastructural_stereotypes:
                    infrastructural = True
                    deciding_stereotype = s
            if infrastructural:
                microservices[m]["stereotype_instances"].append("infrastructural")
                microservices[m]["type"] = "service"
                if deciding_stereotype:
                    trace = dict()
                    trace["parent_item"] = microservices[m]["servicename"]
                    trace["item"] = "infrastructural"
                    trace["file"] = "heuristic, based on stereotype " + deciding_stereotype
                    trace["line"] = "heuristic, based on stereotype " + deciding_stereotype
                    trace["span"] = "heuristic, based on stereotype " + deciding_stereotype
                    traceability.add_trace(trace)
            else:
                microservices[m]["type"] = "service"
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("internal")
                else:
                    microservices[m]["stereotype_instances"] = ["internal"]

                trace = dict()
                trace["parent_item"] = microservices[m]["servicename"]
                trace["item"] = "internal"
                trace["file"] = "heuristic"
                trace["line"] = "heuristic"
                trace["span"] = "heuristic"
                traceability.add_trace(trace)


    return microservices
