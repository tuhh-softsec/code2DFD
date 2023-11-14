import ast

import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.logger as logger
import output_generators.traceability as traceability
import tmp.tmp as tmp


def set_information_flows(dfd) -> dict:
    """Goes through outgoing endpoints and matches them against incoming ones.
    """

    if not used_in_application():
        return

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    incoming_endpoints = get_incoming_endpoints(dfd)
    add_endpoints_tagged_values(incoming_endpoints, dfd)
    outgoing_endpoints, information_flows = get_outgoing_endpoints(information_flows, dfd)
    new_information_flows = match_incoming_to_outgoing_endpoints(incoming_endpoints, outgoing_endpoints, dfd)

    for ni in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = new_information_flows[ni]

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))
    return information_flows


def used_in_application():
    if len(fi.search_keywords("RestTemplate")) > 0:
        return True
    return False


def get_incoming_endpoints(dfd) -> list:
    """Returns incoming API-endpoints of a repository using RestTemplate. Detection based on keywords '@[Request, Post, Get, Patch, Delete, Put]Mapping'
    """

    endpoints = set()
    files = fi.search_keywords("RequestMapping")

    for file in files.keys():

        f = files[file]
        if f["name"].split(".")[-1] != "java":
            continue
        else:
            service = tech_sw.detect_microservice(f["path"], dfd)

            bracket_count = 0               # variable for number of curly brackets to detect nested @RequestMappings
            current_parts = []              # list of "parts" of the path (e.g. /a/b/c -> ["a", "b", "c"])
            last_bc = -1                    # var to compare against last added endpoint

            for l in range(len(f["content"])):
                line = f["content"][l]
                mappings = ["RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping"]
                mapping_in_line = False
                for m in mappings:
                    if m in line:
                        mapping_in_line = True
                        method = m.split("Mapping")[0]
                if mapping_in_line and not "import" in line:
                    endpoint_part = extract_endpoint_part(line)

                # manages the list of path-parts
                    if bracket_count > last_bc:
                        current_parts.append(endpoint_part)
                    elif bracket_count == last_bc:
                        current_parts = current_parts[:-1]
                        current_parts.append(endpoint_part)
                    elif bracket_count < last_bc:
                        dif = last_bc - bracket_count
                        current_parts = current_parts[:-dif]
                        current_parts.append(endpoint_part)

                # adds new endpoint
                    complete_endpoint = "/" + ("".join(current_parts).strip("/"))
                    if not complete_endpoint in [a for (a, b, c, d, e, f) in endpoints if b == service]:
                        endpoints.add((complete_endpoint, service, method, files[file]["path"], files[file]["line_nr"], files[file]["span"]))

                    last_bc = bracket_count

                bracket_count = adjust_bracket_count(bracket_count, line)

    tmp.tmp_config.set("DFD", "endpoints", str(endpoints))
    return endpoints


def extract_endpoint_part(line: str) -> str:
    endpoint_part = ""
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


def add_endpoints_tagged_values(endpoint_tuples: list, dfd):
    """Adds tagged values containing the endpoitns to the microservices.
    """

    microservices = tech_sw.get_microservices(dfd)
    ordered_endpoints = dict()

    for endpoint_tuple in endpoint_tuples:
        if endpoint_tuple[1] in ordered_endpoints.keys():
            ordered_endpoints[endpoint_tuple[1]].add(endpoint_tuple[0])
        else:
            ordered_endpoints[endpoint_tuple[1]] = {endpoint_tuple[0]}

    for endpoint in ordered_endpoints.keys():
        for m in microservices.keys():
            if microservices[m]["servicename"] == endpoint:
                if "tagged_values" in microservices[m].keys():
                    microservices[m]["tagged_values"].append(('Endpoints', list(ordered_endpoints[endpoint])))
                else:
                    microservices[m]["tagged_values"] = [('Endpoints', list(ordered_endpoints[endpoint]))]
    tmp.tmp_config.set("DFD", "microservices", str(microservices))


def get_outgoing_endpoints(information_flows: dict, dfd) -> set:
    """Finds API calls from one service to another if restTemplate.exchange() is used in the application.
    """

    microservices = tech_sw.get_microservices(dfd)

    if microservices != None:
        microservices = [microservices[x]["servicename"] for x in microservices.keys()]
    else:
        microservices = list()
    outgoing_endpoints = set()

    commands = ["restTemplate.exchange", "restTemplate.getForObject"]
    for command in commands:
        files = fi.search_keywords(command)
        for file in files.keys():
            f = files[file]
            if "README" in f["name"] or "test" in f["path"].casefold():
                continue
            microservice = tech_sw.detect_microservice(f["path"], dfd)
            for line in range(len(f["content"])):
                if command in f["content"][line]:
                    func_inp = f["content"][line].split(command)[1]
                    if "," in func_inp:
                        new_outgoing_endpoint = func_inp.split(",")[0].strip()
                        line_nr = line
                    else:           # commands is multiline, looking for comma in next lines
                        found = False
                        i = 0
                        while not found and i < (len(f["content"]) - line):
                            if "," in f["content"][line + i]:
                                new_outgoing_endpoint = f["content"][line + i].split(",")[0].strip()
                                found = True
                                line_nr = line + i
                            i += 1

                    new_outgoing_endpoint, information_flows = find_rst_variable(new_outgoing_endpoint, f, line_nr, information_flows, microservice, dfd)
                    if new_outgoing_endpoint:
                        outgoing_endpoints.add((new_outgoing_endpoint, microservice,  files[file]["path"], files[file]["line_nr"], files[file]["span"]))
                    else:
                        logger.write_log_message("\t\tSomething didn't work", "debug")

    return outgoing_endpoints, information_flows


def find_rst_variable(parameter: str, file: dict, line_nr: int, information_flows: dict, microservice: str, dfd):

    # check if service name in parameter, if yes, add flow directly
    microservices = tech_sw.get_microservices(dfd)
    for m in microservices.keys():
        if microservices[m]["servicename"] in parameter:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = microservice
            information_flows[id]["receiver"] = microservices[m]["servicename"]
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            trace = dict()
            trace["item"] = microservice + " -> " + microservices[m]["servicename"]
            trace["file"] = file["path"]
            trace["line"] = file["line_nr"]
            trace["span"] = file["span"]
            traceability.add_trace(trace)

    variable = False
    if "+" in parameter:    # string consisting of multiple parts
        parameters = parameter.split("+")
    else:           # only one part, but put it in list to make compatible with multi-part-case
        parameters = [parameter]

    for p in range(len(parameters)):    # Treat each part individually
        parameters[p] = parameters[p].strip()
        if "(" in parameters[p] or ")" in parameters[p]:
            logger.write_log_message("\tPart of the string is return value of a function. Can not determine this statically.", "debug")
            return False, information_flows
        elif check_if_variable_is_input(parameters[p], file, line_nr):
            parameters[p] = "{" + parameters[p] + "}"
        elif parameters[p][0] == "\"" and parameters[p][-1] == "\"" and parameters[p].count("\"") == 2:     # it's a string, no change needed
            parameters[p] = parameters[p].strip().strip("\"")
        elif "." in parameters[p]:               # means that it refers to some other file or class -> look for that file, then go through lines
            try:
                parameter_variable = parameters[p].split(".")[-1]
                parameter_class = parameters[p].split(".")[-2]
                files_containing_class = fi.search_keywords("class " + str(parameter_class))
                correct_file = None
                for filec in files_containing_class.keys():
                    fc = files_containing_class[filec]
                    for linec in range(len(fc["content"])):
                        if "class" in fc["content"][linec] and parameter_class in fc["content"][linec]:
                            correct_file = fc["name"]
                            inside_class_definition = True
                            lines_class = len(fc["content"]) - linec
                            i = 0
                            while inside_class_definition and i < lines_class:
                                if "}" in fc["content"][i]:
                                    inside_class_definition = False
                                i += 1
                                if parameter_variable in fc["content"][linec + i] and "=" in fc["content"][linec + i]:
                                    parameters[p] = fc["content"][linec + i].split("=")[1].strip().strip(";").strip().strip("\"")
                                    print("\t\tFound " + str(parameters[p]) + " in file " + str(correct_file))
                                    if parameters[p][0] != "\"" or parameters[p][-1] != "\"":
                                        parameters[p], x = find_rst_variable(parameters[p], fc, linec)     # recursive step
            except:
                print("\tCould not find a definition for " + str(parameters[p]) + ".")
                return False, information_flows
        else:           # means that it's a variable in this file -> go through lines to find it
            found = False
            line = 0
            parameter_variable = parameters[p]
            while found == False and line < len(file["content"]):
                # Assignment of var
                if parameter_variable in file["content"][line] and "=" in file["content"][line]:
                    parameters[p] = file["content"][line].split("=")[1].strip().strip(";").strip()
                    if parameters[p].strip("\"").strip() != "":
                        if parameters[p][0] != "\"" or parameters[p][-1] != "\"":
                            parameters[p], x = find_rst_variable(parameters[p], file, line)      # recursive step
                        if parameters[p] != False:
                            parameters[p] = parameters[p].strip("\"").strip()
                            logger.write_log_message("\t\tFound " + str(parameters[p]) + " in this file.", "info")
                        found = True
                # Var injection via @Value
                elif parameter_variable in file["content"][line]:
                    if "@Value" in file["content"][line - 1]:
                        # injected = file["content"][line - 1].split("@Value(")[1].strip(")")
                        # look in config file
                        pass

                line += 1
            if found == False:
                print("\tCould not find a definition for " + str(parameters[p]) + ".")
                return False, information_flows
    invalid = False
    for p in parameters:
        if p == None or p == False:
            invalid = True
    if not invalid:
        variable = "".join(parameters)      # put together parts for complete URL
    return variable, information_flows


def check_if_variable_is_input(variable: str, file, line_nr: int) -> bool:
    """Detects if a string in a given line is an input parameter.
    """

    open_curly_brackets = 0
    while open_curly_brackets != 1 and line_nr > 0:
        line = file["content"][line_nr]
        if "}" in line:
            open_curly_brackets -= 1
        if "{" in line:
            open_curly_brackets += 1
        if open_curly_brackets == 1:
            if "if" in line or "else" in line or "else if" in line:
                open_curly_brackets -= 1
        if open_curly_brackets == 1:
            inputs = line.split("{")[0].strip().split("(")[-1].strip().strip(")").strip().split(",")
            for i in inputs:
                if variable in i:
                    return True
        line_nr -= 1
    return False


def match_incoming_to_outgoing_endpoints(incoming_endpoints: list, outgoing_endpoints: list, dfd) -> dict:
    """ Find information flows by matching incomgin to outgoing endpoints. Returns list of flows.
    """

    microservices = tech_sw.get_microservices(dfd)
    information_flows_set = set()
    information_flows = dict()
    for o in outgoing_endpoints:
        for i in incoming_endpoints:
            if i[0] in o[0] and i[1] in o[0]:
                information_flows_set.add((o[1], i[1], i[0]))       # (sending service, receiving service, receving endpoint)

                trace = dict()
                trace["item"] = o[0] + " -> " + i[1]
                trace["file"] = o[2]
                trace["line"] = o[3]
                trace["span"] = o[4]
                traceability.add_trace(trace)

    # turn it into dict
    for i in information_flows_set:

        # check for load balancer, circuit breaker, authentication, and SSL
        stereotype_instances = list()
        stereotype_instances.append("restful_http")
        tagged_values = list()
        for m in microservices.keys():
            if microservices[m]["servicename"] == i[0]:
                for prop in microservices[m]["properties"]:
                    if prop[0] == "load_balancer":
                        stereotype_instances.append("load_balanced_link")
                        tagged_values.append(("Load Balancer", prop[1]))
                    elif prop[0] == "circuit_breaker":
                        stereotype_instances.append("circuit_breaker_link")
                        tagged_values.append(("Circuit Breaker", prop[1]))
                for s in microservices[m]["stereotype_instances"]:
                    if s == "authentication_scope_all_requests":
                        stereotype_instances.append("authenticated_request")
                    elif s == "ssl_enabled":
                        stereotype_instances.append("ssl_secured")

        # set flow
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = dict()

        information_flows[id]["sender"] = i[0]
        information_flows[id]["receiver"] = i[1]
        information_flows[id]["endpoint"] = i[2]

        if stereotype_instances:
            information_flows[id]["stereotype_instances"] = stereotype_instances
            information_flows[id]["tagged_values"] = tagged_values



    return information_flows
