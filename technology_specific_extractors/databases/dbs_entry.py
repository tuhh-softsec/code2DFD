import core.file_interaction as fi
import output_generators.traceability as traceability

def detect_databases(microservices: dict) -> dict:
    """Detects databases.
    """

    for m in microservices.keys():
        database = False
        if "image" in microservices[m]:
            if "mongo:" in microservices[m]["image"]:
                database = "MongoDB"
            elif "mysql-server:" in microservices[m]["image"]:
                database = "MySQL"

        if database:
            microservices[m]["type"] == "database_component"
            if "stereotype_instances" in microservices[m]:
                microservices[m]["stereotype_instances"].append("database")
            else:
                microservices[m]["stereotype_instances"] = ["database"]
            if "tagged_values" in microservices[m]:
                microservices[m]["tagged_values"].append(("Database", database))
            else:
                microservices[m]["tagged_values"] = [("Database", database)]

            trace = dict()
            trace["parent_item"] = microservices[m]["servicename"]
            trace["item"] = "database"
            trace["file"] = "heuristic, based on image"
            trace["line"] = "heuristic, based on image"
            trace["span"] = "heuristic, based on image"
            traceability.add_trace(trace)
        else:
            microservices = detect_via_docker(microservices, m)

    return microservices


def detect_via_docker(microservices: dict, m: int) -> dict:
    """Checks microservifces' build paths for dockerfile. If found, parses for possible databases.
    """

    path = microservices[m]["image"]
    dockerfile_lines = fi.check_dockerfile(path)

    database = False
    if dockerfile_lines:
        for line in dockerfile_lines:
            if "FROM" in line:
                if "mongo" in line:
                    database = "MongoDB"
                elif "postgres" in line:
                    database = "PostgreSQL"
    if database:
        microservices[m]["type"] = "database_component"
        try:
            microservices[m]["stereotype_instances"].append("database")
        except:
            microservices[m]["stereotype_instances"] = ["database"]
        try:
            microservices[m]["tagged_values"].append(("Database", database))
        except:
            microservices[m]["tagged_values"] = [("Database", database)]
        trace = dict()
        trace["parent_item"] = microservices[m]["servicename"]
        trace["item"] = "database"
        trace["file"] = "heuristic, based on Dockerfile base image"
        trace["line"] = "heuristic, based on Dockerfile base image"
        trace["span"] = "heuristic, based on Dockerfile base image"
        traceability.add_trace(trace)

    return microservices
