
def detect_ssl_services(microservices: dict) -> dict:
    """Checks if services have ssl enabled.
    """

    for m in microservices.keys():
        for prop in microservices[m]["properties"]:
            if prop[0] == "ssl_enabled":
                if not bool(prop[1]):
                    try:
                        microservices[m]["stereotype_instances"].append("ssl_disabled")
                    except:
                        microservices[m]["stereotype_instances"] = ["ssl_disabled"]

                elif bool(prop[1]):
                    try:
                        microservices[m]["stereotype_instances"].append("ssl_enabled")
                    except:
                        microservices[m]["stereotype_instances"] = ["ssl_enabled"]
            elif prop[0] == "ssl_protocol":
                try:
                    microservices[m]["tagged_values"].append(("SSL Protocol", prop[1]))
                except:
                    microservices[m]["tagged_values"] = [("SSL Protocol", prop[1])]

    return microservices
