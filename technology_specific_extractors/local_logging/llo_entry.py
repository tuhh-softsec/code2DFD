import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_local_logging(microservices: dict, information_flows: dict) -> dict:
    """Detects if a service performs local logging.
    """

    microservices = detect_loggerfactory(microservices)
    microservices = detect_lombok(microservices)

    return microservices, information_flows


def detect_loggerfactory(microservices: dict) -> dict:
    """Detects logging directly via loggerfactory.
    """

    results = fi.search_keywords("LoggerFactory")
    for r in results.keys():
        found = False
        if "test" in results[r]["path"].casefold():
            continue
        microservice = tech_sw.detect_microservice(results[r]["path"])
        for line in results[r]["content"]:
            if "LoggerFactory" in line:
                if "LoggerFactory.getLogger" in line and "=" in line:
                    logger = line.split("=")[0].strip().split(" ")[-1]
                    for line2 in results[r]["content"]:
                        for c in ["info", "error", "debug", "trace", "warn"]:
                            if (logger.casefold() + "." + c) in line2.casefold():       # logger is used -> find mciroservice and add stereotype
                                for m in microservices.keys():
                                    if microservices[m]["servicename"] == microservice:
                                        try:
                                            microservices[m]["stereotype_instances"] += ["local_logging"]
                                        except:
                                            microservices[m]["stereotype_instances"] = ["local_logging"]
                                        found = True
                                        break
                                    if found: break
                            if found: break
                    if found: break
                if found: break

    return microservices


def detect_lombok(microservices: dict) -> dict:
    """Detects logging with Lombok.
    """

    annotations = ["Slf4j", "Log", "Log4j2", "CommonsLog"]
    for annotation in annotations:
        results = fi.search_keywords(annotation)
        for r in results.keys():
            if "test" in results[r]["path"].casefold():
                continue

            annotation_found = False
            use_found = False

            for line in results[r]["content"]:
                if "@" + annotation in line:
                    annotation_found = True
                else:
                    for c in ["info", "error", "debug", "trace", "warn"]:
                        if ("log." + c) in line.casefold():
                            use_found = True

            if annotation_found and use_found:
                microservice = tech_sw.detect_microservice(results[r]["path"])
                for m in microservices.keys():
                    if microservices[m]["servicename"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("local_logging")
                        except:
                            microservices[m]["stereotype_instances"] = ["local_logging"]
                        try:
                            microservices[m]["tagged_values"].append(("Logging Technology", "Lombok"))
                        except:
                            microservices[m]["tagged_values"] = [("Logging Technology", "Lombok")]

    return microservices
