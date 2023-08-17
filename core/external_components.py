import output_generators.traceability as traceability


def add_user(external_components: dict) -> dict:
    """Adds an user to the external components.
    """

    try:
        id = max(external_components.keys()) + 1
    except:
        id = 0
    external_components[id] = dict()
    external_components[id]["name"] = "user"
    external_components[id]["type"] = "external_component"
    external_components[id]["stereotype_instances"] = ["user_stereotype", "entrypoint", "exitpoint"]

    trace = dict()
    trace["item"] = "user"
    trace["file"] = "implicit"
    trace["line"] = "implicit"
    trace["span"] = "implicit"

    traceability.add_trace(trace)

    trace["parent_item"] = "user"
    trace["item"] = "user_stereotype"
    trace["file"] = "implicit"
    trace["line"] = "implicit"
    trace["span"] = "implicit"

    traceability.add_trace(trace)

    trace["parent_item"] = "user"
    trace["item"] = "entrypoint"
    trace["file"] = "heuristic"
    trace["line"] = "heuristic"
    trace["span"] = "heuristic"

    traceability.add_trace(trace)

    trace["parent_item"] = "user"
    trace["item"] = "exitpoint"
    trace["file"] = "heuristic"
    trace["line"] = "heuristic"
    trace["span"] = "heuristic"

    traceability.add_trace(trace)

    return external_components


def add_user_connections(information_flows: dict, microservice: str) -> dict:

    try:
        id = max(information_flows.keys()) + 1
    except:
        id = 0
    information_flows[id] = dict()
    information_flows[id]["sender"] = "user"
    information_flows[id]["receiver"] = microservice
    information_flows[id]["stereotype_instances"] = ["restful_http"]
    information_flows[id + 1] = dict()
    information_flows[id + 1]["sender"] = microservice
    information_flows[id + 1]["receiver"] = "user"
    information_flows[id + 1]["stereotype_instances"] = ["restful_http"]

    trace = dict()
    trace["item"] = "user -> " + microservice
    trace["file"] = "implicit"
    trace["line"] = "implicit"
    trace["span"] = "implicit"
    traceability.add_trace(trace)

    trace["item"] = microservice + " -> user"
    traceability.add_trace(trace)

    return information_flows
