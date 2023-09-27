import core.file_interaction as fi
import core.parse_files as parse
import technology_specific_extractors.environment_variables as env
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def detect_spring_config(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Detects Spring Cloud Config server and connections to it. And parses config files.
    """

    config_server, config_path = False, False
    microservices, config_server, config_path, config_file_path, config_repo_uri, config_server_ports, config_file_path_local = detect_config_server(microservices, dfd)
    if config_file_path or config_repo_uri or config_file_path_local:
        microservices, information_flows, external_components = parse_config_files(config_server, config_path, config_file_path, config_file_path_local, config_repo_uri, microservices, information_flows, external_components)
    microservices, information_flows = detect_config_clients(microservices, information_flows, config_server, config_server_ports)

    return microservices, information_flows, external_components


def detect_config_server(microservices: dict, dfd):
    """Finds config server and sets needed variables
    """

    results = fi.search_keywords("@EnableConfigServer")
    config_server = False
    config_path = False
    config_file_path = False
    config_repo_uri = False
    config_server_ports = list()
    config_file_path_local = False

    if len(results) > 1:
        print("More than one config server. Picking first one found.")
    for r in results.keys():
        config_server = tech_sw.detect_microservice(results[r]["path"], dfd)

        for m in microservices.keys():
            if microservices[m]["servicename"] == config_server:
                try:
                    microservices[m]["stereotype_instances"].append("configuration_server")
                except:
                    microservices[m]["stereotype_instances"] = ["configuration_server"]
                try:
                    microservices[m]["tagged_values"].append(("Configuration Server", "Spring Cloud Config"))
                except:
                    microservices[m]["tagged_values"] = [("Configuration Server", "Spring Cloud Config")]

                # Traceability
                trace = dict()
                trace["parent_item"] = config_server
                trace["item"] = "configuration_server"
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

                try:
                    config_path = ("/").join(microservices[m]["pom_path"].split("/")[:-1])
                except:
                    pass

                for prop in microservices[m]["properties"]:
                    if prop[0] == "config_file_path":
                        config_file_path = prop[1]
                    elif prop[0] == "config_repo_uri":
                        config_repo_uri = prop[1]

                        trace = dict()
                        trace["item"] = "github-repository"
                        trace["file"] = prop[2][0]
                        trace["line"] = prop[2][1]
                        trace["span"] = prop[2][2]

                        traceability.add_trace(trace)

                        trace = dict()
                        trace["item"] = "github-repository -> " + config_server
                        trace["file"] = prop[2][0]
                        trace["line"] = prop[2][1]
                        trace["span"] = prop[2][2]

                        traceability.add_trace(trace)

                    elif prop[0] == "config_file_path_local":
                        config_file_path_local = prop[1]
                    elif prop[0] == "port":
                        config_server_ports.append(prop[1])
    return microservices, config_server, config_path, config_file_path, config_repo_uri, config_server_ports, config_file_path_local


def detect_config_clients(microservices: dict, information_flows: dict, config_server: str, config_server_ports: list) -> dict:
    """Detect microservices that access config server.
    """

    config_id = False
    trace_file = False

    for m in microservices.keys():
        if microservices[m]["servicename"] == config_server:
            config_id = m
        config_uri, config_connected, config_username, config_password = False, False, False, False
        for prop in microservices[m]["properties"]:
            if prop[0] == "config_uri":
                config_uri = prop[1]
                trace_file = prop[2][0]
                trace_line = prop[2][1]
                trace_span = prop[2][2]
            elif prop[0] == "config_connected":
                config_connected = True
                trace_file = prop[2][0]
                trace_line = prop[2][1]
                trace_span = prop[2][2]
            elif prop[0] == "config_username":
                config_username = env.resolve_env_var(prop[1])
                trace_file = prop[2][0]
                trace_line = prop[2][1]
                trace_span = prop[2][2]
            elif prop[0] == "config_password":
                config_password = env.resolve_env_var(prop[1])
                trace_file = prop[2][0]
                trace_line = prop[2][1]
                trace_span = prop[2][2]
        # pw & user

        if not config_connected and config_uri:
            parts = config_uri.split("/")
            for part in parts:
                try:
                    if str(part.split(":")[0]) == str(config_server):
                        config_connected = True
                    elif ":" in part and int(part.split(":")[1]) in config_server_ports:
                        config_connected = True
                except Exception:
                    pass
        if not config_connected and config_uri:
            for port in config_server_ports:
                if "localhost:" + str(port) in config_uri:
                    config_connected = True
        if config_connected:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = config_server
            information_flows[id]["receiver"] = microservices[m]["servicename"]
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            if trace_file:
                trace = dict()
                trace["item"] = config_server + " -> " + microservices[m]["servicename"]
                trace["file"] = trace_file
                trace["line"] = trace_line
                trace["span"] = trace_span
                traceability.add_trace(trace)

            if config_username:
                information_flows[id]["stereotype_instances"].append("plaintext_credentials_link")
                if config_id:
                    if "stereotype_instances" in microservices[config_id]:
                        microservices[config_id]["stereotype_instances"].append("plaintext_credentials")
                    else:
                        microservices[config_id]["stereotype_instances"] = ["plaintext_credentials"]

                    if "tagged_values" in microservices[config_id]:
                        microservices[config_id]["tagged_values"].append(("Username", config_username))
                    else:
                        microservices[config_id]["tagged_values"] = [("Username", config_username)]

                    if trace_file:
                        trace = dict()
                        trace["parent_item"] = microservices[config_id]["servicename"]
                        trace["item"] = "plaintext_credentials"
                        trace["file"] = trace_file
                        trace["line"] = trace_line
                        trace["span"] = trace_span
                        traceability.add_trace(trace)

            if config_password:
                information_flows[id]["stereotype_instances"].append("plaintext_credentials_link")
                if config_id:
                    if "stereotype_instances" in microservices[config_id]:
                        microservices[config_id]["stereotype_instances"].append("plaintext_credentials")
                    else:
                        microservices[config_id]["stereotype_instances"] = ["plaintext_credentials"]

                    if "tagged_values" in microservices[config_id]:
                        microservices[config_id]["tagged_values"].append(("Password", config_password))
                    else:
                        microservices[config_id]["tagged_values"] = [("Password", config_password)]

                    if trace_file:
                        trace = dict()
                        trace["parent_item"] = microservices[config_id]["servicename"]
                        trace["item"] = "plaintext_credentials"
                        trace["file"] = trace_file
                        trace["line"] = trace_line
                        trace["span"] = trace_span
                        traceability.add_trace(trace)

    return microservices, information_flows


def parse_config_files(config_server: str, config_path: str, config_file_path: str, config_file_path_local: str, config_repo_uri: str, microservices: dict, information_flows: dict, external_components: dict) -> dict:
    """Parses config files from locally or other GitHub repository.
    """

    if not config_file_path:
        config_file_path = ""
    if config_repo_uri:
        information_flows, external_components = set_repo(information_flows, external_components, config_repo_uri, config_server)
        repo_path = config_repo_uri.split("github.com/")[1].split(".")[0]
    else:
        repo_path = tmp.tmp_config["Repository"]["path"]
    gh_contents = False
    contents = set()

    if config_file_path:
        new_contents = fi.get_repo_contents_local(repo_path, config_file_path)
        for file in new_contents:
            contents.add(file)

    else:
        new_contents = fi.get_repo_contents_local(repo_path, False)
        for file in new_contents:
            contents.add(file)

    # external (other github repository) didn't work, look locally
    if config_file_path_local:

        repo_path = tmp.tmp_config["Repository"]["path"]
        config_file_path_local = config_file_path_local.split("/".join(repo_path.split("/")[1:]))[1].strip("./")

        new_contents = fi.get_repo_contents_local(repo_path, config_file_path_local)
        for file in new_contents:
            contents.add(file)


    if not gh_contents and not contents:
        repo_path = tmp.tmp_config["Repository"]["path"]

        new_contents = fi.get_repo_contents_local(repo_path, config_file_path)
        for file in new_contents:
            contents.add(file)

    if gh_contents:
        for file in gh_contents:
            contents.add((file.name, file.download_url, file.path))

    if contents:
        for file in contents:
            ending = False
            microservice = False
            properties = set()
            for m in microservices.keys():
                if file[0].split(".")[0] == microservices[m]["servicename"]:
                    microservice = microservices[m]["servicename"]
                    correct_id = m
                    if "." in file[0]:
                        ending = file[0].split(".")[1]
                    break
            if not microservice:
                for m in microservices.keys():
                    if  microservices[m]["servicename"] in file[0].split(".")[0]:
                        microservice = microservices[m]["servicename"]
                        correct_id = m
                        if "." in file[0]:
                            ending = file[0].split(".")[1]
                        break
            if microservice:
                if ending:
                    if ending == "yml" or ending == "yaml":
                        name, properties = parse.parse_yaml_file(file[1], file[2])
                        name = name[0]
                    elif ending == "properties":
                        name, properties = parse.parse_properties_file(file[1])
                        name = name[0]
                    if "properties" in microservices[correct_id]:
                        microservices[correct_id]["properties"] |= properties
                    else:
                        microservices[correct_id]["properties"] = properties

    return microservices, information_flows, external_components


def set_repo(information_flows: dict, external_components: dict, config_repo_uri: str, config_server: str) -> dict:
    """Adds a repo to the external components.
    """

    try:
        id = max(information_flows.keys()) + 1
    except:
        id = 0
    information_flows[id] = dict()
    information_flows[id]["sender"] = "github-repository"
    information_flows[id]["receiver"] = config_server
    information_flows[id]["stereotype_instances"] = ["restful_http"]

    try:
        id = max(external_components.keys()) + 1
    except:
        id = 0
    external_components[id] = dict()
    external_components[id]["name"] = "github-repository"
    external_components[id]["type"] = "external_component"
    external_components[id]["stereotype_instances"] = ["github_repository", "entrypoint"]
    external_components[id]["tagged_values"] = [("URL", config_repo_uri)]

    return information_flows, external_components
