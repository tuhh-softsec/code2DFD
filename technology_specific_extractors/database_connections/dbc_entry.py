import ast

import technology_specific_extractors.environment_variables as env
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def set_information_flows(dfd) -> set:
    """Goes through services and checks if there are connections to databases.
    """

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    if tmp.tmp_config.has_option("DFD", "external_components"):
        external_components = ast.literal_eval(tmp.tmp_config["DFD"]["external_components"])
    else:
        external_components = dict()

    microservices = tech_sw.get_microservices(dfd)

    microservices, information_flows, external_components = check_properties(microservices, information_flows, external_components)

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))
    tmp.tmp_config.set("DFD", "microservices", str(microservices))
    tmp.tmp_config.set("DFD", "external_components", str(external_components))
    return microservices, information_flows


def get_information_flows(microservices: dict, information_flows: dict, external_components: dict) -> dict:

    microservices, information_flows, external_components = check_properties(microservices, information_flows, external_components)

    return microservices, information_flows, external_components


def check_properties(microservices: dict, information_flows: dict, external_components: dict) -> dict:
    """Checks microservices' properties for connection details to datasources. If found, sets these connections.
    """

    for m in microservices.keys():
        database_service, username, password, database_url = False, False, False, False
        trace_info = (False, False, False)
        sender = microservices[m]["servicename"]
        for prop in microservices[m]["properties"]:
            if prop[0] == "datasource_url":
                trace_info = (prop[2][0], prop[2][1], prop[2][2])
                if "mem:" in prop[1]:    # in-memory database
                    pass
                else:
                    database_url = prop[1]
                    parts = database_url.split("/")
                    for mi in microservices.keys():
                        if microservices[mi]["servicename"] in parts:
                            database_service = microservices[mi]["servicename"]
            elif prop[0] == "datasource_host":
                trace_info = (prop[2][0], prop[2][1], prop[2][2])
                for mi in microservices.keys():
                    if microservices[mi]["servicename"] == prop[1]:
                        database_service = microservices[mi]["servicename"]
            elif prop[0] == "datasource_uri":
                trace_info = (prop[2][0], prop[2][1], prop[2][2])
                database = prop[1].split("://")[1].split("/")[0]
                for mi in microservices.keys():
                    if microservices[mi]["servicename"] == database:
                        database_service = microservices[mi]["servicename"]
            if prop[0] == "datasource_username":
                username = env.resolve_env_var(prop[1])
            if prop[0] == "datasource_password":
                password = env.resolve_env_var(prop[1])

        if database_service:    # found a connection to a microservice
            # set information flow
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = database_service
            information_flows[id]["receiver"] = sender
            information_flows[id]["stereotype_instances"] = ["jdbc"]
            if password:
                try:
                    information_flows[id]["tagged_values"].append(("Password", password.strip()))
                except:
                    information_flows[id]["tagged_values"] = [("Password", password.strip())]
            if username:
                try:
                    information_flows[id]["tagged_values"].append(("Username", username.strip()))
                except:
                    information_flows[id]["tagged_values"] = [("Username", username.strip())]
            if username or password:
                information_flows[id]["stereotype_instances"].append("plaintext_credentials_link")

            trace = dict()
            trace["item"] = database_service + " -> " + sender
            trace["file"] = trace_info[0]
            trace["line"] = trace_info[1]
            trace["span"] = trace_info[2]

            traceability.add_trace(trace)

            # adjust service to database
            for id in microservices.keys():

                if microservices[id]["servicename"] == database_service:
                    microservices[id]["type"] = "database_component"
                    if "stereotype_instances" in microservices[id]:
                        microservices[id]["stereotype_instances"].append("database")
                    else:
                        microservices[id]["stereotype_instances"] = ["database"]
                    if password:
                        microservices[id]["stereotype_instances"].append("plaintext_credentials")
                        if "tagged_values" in microservices[id]:
                            microservices[id]["tagged_values"].append(("Password", password.strip()))
                        else:
                            microservices[id]["tagged_values"] = [("Password", password.strip())]
                    if username:
                        microservices[id]["stereotype_instances"].append("plaintext_credentials")
                        if "tagged_values" in microservices[id]:
                            microservices[id]["tagged_values"].append(("Username", username.strip()))
                        else:
                            microservices[id]["tagged_values"] = [("Username", username.strip())]

            # check if information flow in other direction exists (can happen faultely in docker-compose)
            for i in information_flows.keys():
                if information_flows[i]["sender"] == sender and information_flows[i]["receiver"] == database_service:
                    information_flows.pop(i)

        elif database_url:  # found a connection to an unknown url

            # determine port if possible
            port = False
            if "localhost:" in database_url:
                port = database_url.split("localhost:")[1].split("/")[0].strip().strip("\"")

            # determines type of DB
            database_type = False
            for prop in microservices[m]["properties"]:
                if prop[0] == "datasource_type":
                    database_type = prop[1]

            if not database_type:
                if "mysql" in database_url.casefold():
                    database_type = "MySQL"
                elif "mongo" in database_url.casefold():
                    database_type = "MongoDB"
                elif "postgres" in database_url.casefold():
                    database_type = "PostgreSQL"
                elif "neo4j" in database_url.casefold():
                    database_type = "Neo4j"

            # create external component
            try:
                id = max(external_components.keys()) + 1
            except:
                id = 0
            external_components[id] = dict()
            external_components[id]["name"] = "database-" + str(microservices[m]["servicename"])
            external_components[id]["type"] = "external_component"
            external_components[id]["stereotype_instances"] = ["entrypoint", "exitpoint", "external_database"]

            trace = dict()
            trace["item"] = "database-" + str(microservices[m]["servicename"])
            trace["file"] = trace_info[0]
            trace["line"] = trace_info[1]
            trace["span"] = trace_info[2]

            traceability.add_trace(trace)

            if database_type:
                external_components[id]["tagged_values"] = [("Database", database_type)]

            if port:
                try:
                    external_components[id]["tagged_values"].append(("Port", port))
                except:
                    external_components[id]["tagged_values"] = [("Port", port)]

            if password:
                if "tagged_values" in external_components[id]:
                    external_components[id]["tagged_values"].append(("Password", password.strip()))
                else:
                    external_components[id]["tagged_values"] = [("Password", password.strip())]
                if "stereotype_instances" in external_components[id]:
                    external_components[id]["stereotype_instances"].append("plaintext_credentials")
                else:
                    external_components[id]["stereotype_instances"] = ["plaintext_credentials"]
            if username:
                try:
                    external_components[id]["tagged_values"].append(("Username", username.strip()))
                except:
                    external_components[id]["tagged_values"] = [("Username", username.strip())]
                try:
                    external_components[id]["stereotype_instances"].append("plaintext_credentials")
                except:
                    external_components[id]["stereotype_instances"] = ["plaintext_credentials"]

            # set information flow
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = "database-" + str(microservices[m]["servicename"])
            information_flows[id]["receiver"] = microservices[m]["servicename"]

            information_flows[id]["stereotype_instances"] = ["jdbc"]
            if username or password:
                information_flows[id]["stereotype_instances"].append("plaintext_credentials_link")

            if password:
                information_flows[id]["tagged_values"] = [("Password", password.strip())]
            if username:
                try:
                    information_flows[id]["tagged_values"].append(("Username", username.strip()))
                except:
                    information_flows[id]["tagged_values"] = [("Username", username.strip())]

            tmp.tmp_config.set("DFD", "external_components", str(external_components))

            trace = dict()
            trace["item"] = "database-" + str(microservices[m]["servicename"]) + " -> " + microservices[m]["servicename"]
            trace["file"] = trace_info[0]
            trace["line"] = trace_info[1]
            trace["span"] = trace_info[2]

            traceability.add_trace(trace)

    return microservices, information_flows, external_components


def clean_database_connections(microservices: dict, information_flows: dict) -> dict:
    """Removes database connections in wrong direction, which can occur from docker compose.
    """

    for m in microservices.keys():
        if microservices[m]["type"] == "database_component":
            to_purge = set()
            for i in information_flows.keys():
                if information_flows[i]["receiver"] == microservices[m]["servicename"]:
                    to_purge.add(i)
            for p in to_purge:
                information_flows.pop(p)

    return information_flows





#
