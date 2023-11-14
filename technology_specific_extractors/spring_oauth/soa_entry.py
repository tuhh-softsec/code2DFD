import core.file_interaction as fi
import technology_specific_extractors.environment_variables as env
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_spring_oauth(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detect Spring OAuth Server and connections to it.
    """

    microservices = detect_authorization_server(microservices, dfd)
    microservices = detect_resource_servers(microservices, dfd)
    microservices, information_flows = detect_token_server(microservices, information_flows, dfd)
    microservices = detect_preauthorized_methods(microservices, dfd)

    return microservices, information_flows


def detect_authorization_server(microservices: dict, dfd) -> dict:
    """Detects an authorization server.
    """

    results = fi.search_keywords("@EnableAuthorizationServer")

    authorization_server = str()
    for r in results.keys():
        authorization_server = tech_sw.detect_microservice(results[r]["path"], dfd)
        for m in microservices.keys():
            if microservices[m]["servicename"] == authorization_server:
                if "stereotype_instances" in microservices[m]:
                    microservices[m]["stereotype_instances"].append("authorization_server")
                else:
                    microservices[m]["stereotype_instances"] = ["authorization_server"]
                if "tagged_values" in microservices[m]:
                    microservices[m]["tagged_values"].append(("Authorization Server", "Spring OAuth2"))
                else:
                    microservices[m]["tagged_values"] = [("Authorization Server", "Spring OAuth2")]

                # Traceability
                trace = dict()
                trace["parent_item"] = authorization_server
                trace["item"] = "authorization_server"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

    return microservices


def detect_resource_servers(microservices: dict, dfd) -> dict:
    """Detects resource servers.
    """

    results = fi.search_keywords("@EnableResourceServer")

    resource_server = str()
    for r in results.keys():
        resource_server = tech_sw.detect_microservice(results[r]["path"], dfd)
        for m in microservices.keys():
            if microservices[m]["servicename"] == resource_server:
                try:
                    microservices[m]["stereotype_instances"].append("resource_server")
                except:
                    microservices[m]["stereotype_instances"] = ["resource_server"]

                # Traceability
                trace = dict()
                trace["parent_item"] = resource_server
                trace["item"] = "resource_server"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

    return microservices


def detect_token_server(microservices: dict, information_flows: dict, dfd) -> dict:
    """Goes thorugh properties of services and detects if one of them is tokenserver for the others.
    """

    for m in microservices.keys():
        token_server = False
        client_secret = False
        for prop in microservices[m]["properties"]:
            if prop[0] == "oauth_client_secret":
                client_secret = env.resolve_env_var(prop[1])
        if client_secret:
            stereotypes = ["authentication_with_plaintext_credentials", "auth_provider", "restful_http", "plaintext_credentials_link"]
            tagged_values = [("Password", client_secret)]
        else:
            stereotypes = ["auth_provider", "restful_http"]
            tagged_values = list()
        for prop in microservices[m]["properties"]:
            if prop[0] == "oauth_tokenuri":
                token_server_uri = prop[1]
                token_server = fi.resolve_url(token_server_uri, False, dfd)
                if token_server:
                    for m2 in microservices.keys():
                        if microservices[m2]["servicename"] == token_server:
                            if "stereotype_instances" in microservices[m2]:
                                microservices[m2]["stereotype_instances"].append("token_server")
                            else:
                                microservices[m2]["stereotype_instances"] = ["token_server"]
                            trace = dict()
                            trace["parent_item"] = microservices[m2]["servicename"]
                            trace["item"] = "token_server"
                            trace["file"] = prop[2][0]
                            trace["line"] = prop[2][1]
                            trace["span"] = prop[2][2]

                            traceability.add_trace(trace)

                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()

                    information_flows[id]["sender"] = token_server
                    information_flows[id]["receiver"] = microservices[m]["servicename"]
                    information_flows[id]["stereotype_instances"] = stereotypes
                    information_flows[id]["tagged_values"] = tagged_values

                    trace = dict()
                    trace["item"] = token_server + " -> " + microservices[m]["servicename"]
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)

    return microservices, information_flows


def detect_preauthorized_methods(microservices: dict, dfd) -> dict:
    """Detects methods annotated as pre-authroized.
    """

    results = fi.search_keywords("@PreAuthorize")

    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        if not "readme" in results[r]["path"].casefold() and not "test" in results[r]["path"].casefold():
            # Try extracting endpoints
            tagged_values = set()
            endpoints = extract_endpoints(results[r]["content"])
            if endpoints:
                tagged_values = [("Pre-authorized Endpoints", endpoints)]

            for m in microservices.keys():
                if microservices[m]["servicename"] == microservice:
                    try:
                        microservices[m]["stereotype_instances"].append("pre_authorized_endpoints")
                    except:
                        microservices[m]["stereotype_instances"] = ["pre_authorized_endpoints"]
                    if tagged_values:
                        try:
                            microservices[m]["tagged_values"] += tagged_values
                        except:
                            microservices[m]["tagged_values"] = tagged_values

                    # Traceability
                    trace = dict()
                    trace["parent_item"] = microservice
                    trace["item"] = "pre_authorized_endpoints"
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)

    return microservices


def extract_endpoints(file_as_lines):
    """Extracts the endpoints that are pre-authorized.
    """

    endpoints = set()
    mappings = ["RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"]

    for line_nr in range(len(file_as_lines)):
        line = file_as_lines[line_nr]
        if "@PreAuthorize" in line:
            endpoint = False
            for mapping in mappings:
                if mapping in file_as_lines[line_nr + 1]:
                    endpoint = extract_endpoint_part(file_as_lines[line_nr + 1])

            if endpoint:
                endpoints.add(endpoint)

    # nested mappings not considered here
    endpoints = list(endpoints)
    return endpoints


def extract_endpoint_part(line: str) -> str:
    endpoint_part = str()
    if "path" in line:          # not found in documentation, but used in piggy to name endpoint
        endpoint_part = line.split("path")[1].split(",")[0].split('\"')[1]
    elif "value" in line:       # usual keyword to describe path
        endpoint_part = line.split("value")[1].split(",")[0].split('\"')[1]
    elif not "," in line and "/" in line:       # only for the "/" endpoint
        endpoint_part = line.split('\"')[1]
    return endpoint_part


def adjust_bracket_count(bracket_count: int, line: str) -> int:
    """Helper function keeping track of number of opened brackets.
    """

    bracket_count += line.count("{")
    bracket_count -= line.count("}")
    return bracket_count
