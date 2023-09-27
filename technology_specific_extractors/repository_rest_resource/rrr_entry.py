import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_endpoints(microservices: dict, dfd) -> dict:
    """Detects endpoints offered via @RepositoryRestResource
    """

    results = fi.search_keywords("@RepositoryRestResource")
    for r in results.keys():
        endpoints = set()
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@RepositoryRestResource" in line:
                if "path" in line:
                    endpoint = line.split("path")[1].split(",")[0].strip().strip("=\"/()").strip()
                    endpoint = "/" + endpoint
                    endpoints.add(endpoint)
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == microservice:
                            try:
                                microservices[m]["tagged_values"].append(("Endpoints", list(endpoints)))
                            except:
                                microservices[m]["tagged_values"] = [("Endpoints", list(endpoints))]
    return microservices
