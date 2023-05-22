import technology_specific_extractors.environment_variables as env


def set_plaintext_credentials(microservices: dict) -> dict:
    """Goes through properties and sets stereotype and tagged values, if plaintext credentials are found.
    """

    for m in microservices.keys():
        plaintext_credentials = False
        tagged_values = set()
        if "properties" in microservices[m] and "stereotype_instances" in microservices[m]:
            for prop in microservices[m]["properties"]:
                if prop[0] == "datasource_password" and "database" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    password = env.resolve_env_var(prop[1])
                    tagged_values.add(("Password", password))
                elif prop[0] == "datasource_username" and "database" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    username = env.resolve_env_var(prop[1])
                    tagged_values.add(("Username", username))

                elif prop[0] == "mail_password" and "mail_server" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    password = env.resolve_env_var(prop[1])
                    tagged_values.add(("Password", password))
                elif prop[0] == "mail_username" and "mail_server" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    username = env.resolve_env_var(prop[1])
                    tagged_values.add(("Username", username))

                elif prop[0] == "config_password" and "configuration_server" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    password = env.resolve_env_var(prop[1])
                    tagged_values.add(("Password", password))
                elif prop[0] == "config_username" and "configuration_server" in microservices[m]["stereotype_instances"]:
                    plaintext_credentials = True
                    username = env.resolve_env_var(prop[1])
                    tagged_values.add(("Username", username))

        if plaintext_credentials:
            if "stereotype_instances" in microservices[m]:
                microservices[m]["stereotype_instances"].append("plaintext_credentials")
            else:
                microservices[m]["stereotype_instances"] = ["plaintext_credentials"]
        if tagged_values:
            if "tagged_values" in microservices[m]:
                microservices[m]["tagged_values"] += tagged_values
            else:
                microservices[m]["tagged_values"] = tagged_values

    return microservices
