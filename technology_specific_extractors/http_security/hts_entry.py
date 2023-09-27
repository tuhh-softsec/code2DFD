import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_authentication_scopes(microservices: dict, dfd) -> dict:
    """Detects authentication scopes via HttpSecurity configurations.
    """

    configuration_tuples = detect_configurations(dfd)
    microservices = interpret_configurations(microservices, configuration_tuples)

    return microservices


def detect_configurations(dfd):
    """Finds httpSecurity configurations.
    """

    configuration_tuples = list()
    configuration_classes = ["AuthenticationManagerBuilder", "HttpSecurity"]
    for c_class in configuration_classes:
        results = fi.search_keywords(c_class)
        for r in results.keys():
            microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
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
                            configurations.add((configuration, results[r]["path"], results[r]["line_nr"], results[r]["span"]))
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
            if "csrf().disable()" in configuration[0] or "csrf.disable()" in configuration[0]:
                stereotypes.append("csrf_disabled")

                trace = dict()
                trace["parent_item"] = configuration_tuple[0]
                trace["item"] = "csrf_disabled"
                trace["file"] = configuration[1]
                trace["line"] = configuration[2]
                trace["span"] = configuration[3]
                traceability.add_trace(trace)
            # unauthenticated access
            if "permitAll()" in configuration[0]:
                scope_restricted = True
            # Basic atuhentication
            if "httpBasic()" in configuration[0]:
                stereotypes.append("basic_authentication")

                trace = dict()
                trace["parent_item"] = configuration_tuple[0]
                trace["item"] = "basic_authentication"
                trace["file"] = configuration[1]
                trace["line"] = configuration[2]
                trace["span"] = configuration[3]
                traceability.add_trace(trace)
            # In Memory authentication
            if "inMemoryAuthentication()" in configuration[0]:
                stereotypes.append("in_memory_authentication")

                trace = dict()
                trace["parent_item"] = configuration_tuple[0]
                trace["item"] = "in_memory_authentication"
                trace["file"] = configuration[1]
                trace["line"] = configuration[2]
                trace["span"] = configuration[3]
                traceability.add_trace(trace)
            # Authentication credentials
            if "withUser(" in configuration[0]:
                username = configuration[0].split("withUser(")[1].split(")")[0].strip("\" ")
                tagged_values.append(("Username", username))
            if "password(" in configuration[0]:
                password = configuration[0].split("password(")[1].split(")")[0].strip("\" ")
                tagged_values.append(("Password", password))
            # Authentication scope
            if "anyRequest().authenticated()" in configuration[0] and not scope_restricted:
                stereotypes.append("authentication_scope_all_requests")

                trace = dict()
                trace["parent_item"] = configuration_tuple[0]
                trace["item"] = "authentication_scope_all_requests"
                trace["file"] = configuration[1]
                trace["line"] = configuration[2]
                trace["span"] = configuration[3]
                traceability.add_trace(trace)

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
