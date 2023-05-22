import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_authentication_scopes(microservices: dict) -> dict:
    """Detects authentication scopes via HttpSecurity configurations.
    """

    configuration_tuples = detect_configurations()
    microservices = interpret_configurations(microservices, configuration_tuples)

    return microservices


def detect_configurations():
    """Finds httpSecurity configurations.
    """

    configuration_tuples = list()
    configuration_classes = ["AuthenticationManagerBuilder", "HttpSecurity"]
    for c_class in configuration_classes:
        results = fi.search_keywords(c_class)
        for r in results.keys():
            microservice = tech_sw.detect_microservice(results[r]["path"])
            configurations = set()
            objects = list()
            for line in results[r]["content"]:
                if "configure(" + c_class in line:
                    objects.append(line.split(c_class)[1].split(")")[0].strip())
            for object in objects:
                for line_nr in range(len(results[r]["content"])):
                    line = results[r]["content"][line_nr]
                    configuration = False
                    if object in line:
                        if ";" in line:
                            configuration = line.split(object)[1].split(";")[0].strip(" .")
                        else:   # multi-line
                            found = False
                            counter = line_nr
                            configuration = line.strip()

                            while not found and counter < len(results[r]["content"]):
                                counter += 1
                                new_line = results[r]["content"][counter]
                                new_line = new_line.strip()

                                if not new_line.strip()[0:2] == "//":
                                    new_configuration = configuration + new_line
                                    configuration = new_configuration

                                if ";" in new_line:
                                    found = True

                    if configuration:
                        configuration = configuration.replace(" ", "")
                        if "{" in configuration:
                            configuration = configuration.split("{")[1]
                        if object + "." in configuration:
                            configurations.add(configuration)
            configuration_tuples.append((microservice, configurations))

    return configuration_tuples


def interpret_configurations(microservices: dict, configuration_tuples: list) -> dict:
    """Translates configurations into stereotypes and tagged values.
    """

    for configuration_tuple in configuration_tuples:
        stereotypes, tagged_values = list(), list()
        # create stereotypes and tagged_values
        for configuration in configuration_tuple[1]:
            scope_restricted = False
            # CSRF
            if "csrf().disable()" in configuration or "csrf.disable()" in configuration:
                stereotypes.append("csrf_disabled")
            # unauthenticated access
            if "permitAll()" in configuration:
                scope_restricted = True
            # Basic atuhentication
            if "httpBasic()" in configuration:
                stereotypes.append("basic_authentication")
            # In Memory authentication
            if "inMemoryAuthentication()" in configuration:
                stereotypes.append("in_memory_authentication")
            # Authentication credentials
            if "withUser(" in configuration:
                username = configuration.split("withUser(")[1].split(")")[0].strip("\" ")
                tagged_values.append(("Username", username))
            if "password(" in configuration:
                password = configuration.split("password(")[1].split(")")[0].strip("\" ")
                tagged_values.append(("Password", password))
            # Authentication scope
            if "anyRequest().authenticated()" in configuration and not scope_restricted:
                stereotypes.append("authentication_scope_all_requests")

        for m in microservices.keys():
            if microservices[m]["servicename"] == configuration_tuple[0]:
                try:
                    microservices[m]["stereotype_instances"] += stereotypes
                except:
                    microservices[m]["stereotype_instances"] = stereotypes
                try:
                    microservices[m]["tagged_values"] += tagged_values
                except:
                    microservices[m]["tagged_values"] = tagged_values

    return microservices
