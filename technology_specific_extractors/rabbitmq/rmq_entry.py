import ast
import re

import yaml

import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


def set_information_flows(dfd) -> set:
    """Connects incoming endpoints, outgoing endpoints, and routings to information flows
    """

    if not used_in_application():
        return

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    new_information_flows = dict()

    routings = get_routings()
    incoming_endpoints = get_incoming_endpoints(dfd)
    outgoing_endpoints = get_outgoing_endpoints(routings, dfd)
    new_information_flows = match_incoming_to_outgoing_endpoints(incoming_endpoints, outgoing_endpoints, dfd)

    # merge old and new flows
    for ni in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = new_information_flows[ni]

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))
    return information_flows


def used_in_application():
    if len(fi.search_keywords("RabbitTemplate")) > 0:
        return True
    return False


def get_routings() -> set:
    """Finds routings defined via RabbitListenerConfigurer
    """

    routings = set()
    files = fi.search_keywords("@RabbitListenerConfigurer")
    for file in files.keys():
        f = files[file]
        for line in range(len(f["content"])):
            if "RabbitListenerConfigurer" in f["content"][line]:
                line_in_configurer = line
                while not "}" in f["content"][line_in_configurer]:
                    line_in_configurer += 1
                    if "exchangeName" in f["content"][line_in_configurer]:
                        exchange = f["content"][line_in_configurer].split("exchangeName")[1].split(";")[0].strip().strip("=").strip().strip("\"")
                    if "routingKeyName" in f["content"][line_in_configurer]:
                        routingKey = f["content"][line_in_configurer].split("routingKeyName")[1].split(";")[0].strip().strip("=").strip().strip("\"")
                routings.add((exchange, routingKey))
    return routings


def get_incoming_endpoints(dfd) -> set:
    """Finds Incoming queues, i.e. instances of RabbitListener
    """

    files = fi.search_keywords("@RabbitListener")
    incoming_queues = set()
    for file in files.keys():
        f = files[file]
        if "README" in f["name"]:
            pass
        else:
            microservice = tech_sw.detect_microservice(f["path"], dfd)
            for line in range(len(f["content"])):
                if "@RabbitListener" in f["content"][line]:
                    new_incoming_queue = f["content"][line].split("queues")[1].split("=")[1].strip().strip(")")
                    new_incoming_queue = fi.find_variable(new_incoming_queue, f)

                    span = re.search("@RabbitListener", f["content"][line])
                    trace = (f["name"], line, span)

                    incoming_queues.add((new_incoming_queue, microservice, trace))
    return incoming_queues


def get_outgoing_endpoints(routings: set, dfd) -> set:
    """Finds points where messages are sent to exchanges via rabbitTemplate.exchange
    """
    outgoing_endpoints = set()
    sending_commands = ["convertAndSend", "convertSendAndReceive", "convertSendAndReceiveAsType", "doSend", "doSendAndReceive", "doSendAndReceiveWithFixed", "doSendAndReceiveWithTemporary", "send", "sendAndReceive"]
    rabbitTemplates = fi.find_instances("RabbitTemplate")
    for template in rabbitTemplates:
        for command in sending_commands:
            files = fi.search_keywords(f"{template}.{command}")
            for file in files.keys():
                f = files[file]
                if "README" in f["name"]:
                    pass
                else:
                    microservice = tech_sw.detect_microservice(f["path"], dfd)
                    for line in range(len(f["content"])):
                        if ("rabbitTemplate." + command) in f["content"][line]: #found correct (starting) line
                            exchange = None
                            routingKey = None
                            if not ";" in f["content"][line]:   # i.e., multi-line command -> search for next line with a semicolon
                                complete_command = f["content"][line]
                                found_semicolon = False
                                i = line + 1
                                while not found_semicolon and i < len(f["content"]):
                                    if ";" in f["content"][i]:
                                        found_semicolon = True
                                    complete_command += f["content"][i]
                                    i += 1
                            else:
                                complete_command = f["content"][line]
                            parameters = "".join(complete_command.split(command)[1]).split(",")
                            for p in range(len(parameters)): #strip and find correct variables
                                parameters[p] = parameters[p].strip().strip(";").strip().strip(")").strip().strip("(").strip()
                                parameters[p] = fi.find_variable(parameters[p], f)
                            found = False
                            i = 0
                            while found == False and i < len(parameters):
                                for r in routings:
                                    if r[0] in parameters[i] or parameters[i] in r[0]:
                                        try:
                                            exchange = parameters[i]
                                            routingKey = parameters[i + 1]
                                        except:
                                            print("Could not extract exchange and routing key from sending-statement")
                                        found = True
                                i += 1

                            span = re.search("rabbitTemplate." + command, f["content"][line])
                            trace = (f["name"], line, span)

                            outgoing_endpoints.add((exchange, routingKey, microservice, trace))
    return outgoing_endpoints


def match_incoming_to_outgoing_endpoints(incoming_endpoints: set, outgoing_endpoints: set, dfd) -> dict:
    """Finds information flows by regexing routing keys of outgoing endpoints to queues of incoming endpoints.
    """

    # outgoing: (exchange, routingkey, microservice, (file, line, span))
    # incoming: (queue, microservice, (file, line, span))

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    microservices = tech_sw.get_microservices(dfd)
    rabbit_server = False
    for id in microservices.keys():
        if ("Message Broker", "RabbitMQ") in microservices[id]["tagged_values"]:
            rabbit_server = microservices[id]["servicename"]
            rabbit_id = id

    if rabbit_server:
        for i in incoming_endpoints:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = rabbit_server
            information_flows[id]["receiver"] = i[1]
            information_flows[id]["stereotype_instances"] = ["restful_http", "message_consumer_rabbitmq"]
            information_flows[id]["tagged_values"] = [("Queue", str(i[0]))]

            # Traceability
            trace = dict()

            trace["item"] = str(rabbit_server) + " -> " + str(i[1])
            trace["file"] = i[2][0]
            trace["line"] = i[2][1]
            trace["span"] = i[2][2]

            traceability.add_trace(trace)

            # Traceability
            trace = dict()
            trace["parent_item"] = str(rabbit_server) + " -> " + str(i[1])
            trace["item"] = "message_consumer_rabbitmq"
            trace["file"] = i[2][0]
            trace["line"] = i[2][1]
            trace["span"] = i[2][2]

            traceability.add_trace(trace)

        for o in outgoing_endpoints:

            username, password, plaintext_credentials = False, False, False

            for m in microservices.keys():
                if microservices[m]["servicename"] == o[2]:
                    if "properties" in microservices[m]:
                        for prop in microservices[m]["properties"]:
                            if prop[0] == "rabbit_username":
                                username = prop[1]
                                plaintext_credentials = True
                                if "stereotype_instances" in microservices[rabbit_id]:
                                    microservices[rabbit_id]["stereotype_instances"].append("plaintext_credentials")
                                else:
                                    microservices[rabbit_id]["stereotype_instances"] = ["plaintext_credentials"]
                                if "tagged_values" in microservices[rabbit_id]:
                                    microservices[rabbit_id]["tagged_values"].append(("Username", username))
                                else:
                                    microservices[rabbit_id]["tagged_values"] = [("Username", username)]

                            elif prop[0] == "rabbit_password":
                                password = prop[1]
                                plaintext_credentials = True
                                if "stereotype_instances" in microservices[rabbit_id]:
                                    microservices[rabbit_id]["stereotype_instances"].append("plaintext_credentials")
                                else:
                                    microservices[rabbit_id]["stereotype_instances"] = ["plaintext_credentials"]
                                if "tagged_values" in microservices[rabbit_id]:
                                    microservices[rabbit_id]["tagged_values"].append(("Password", password))
                                else:
                                    microservices[rabbit_id]["tagged_values"] = [("Password", password)]

            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = o[2]
            information_flows[id]["receiver"] = rabbit_server
            information_flows[id]["stereotype_instances"] = ["restful_http", "message_producer_rabbitmq"]
            if plaintext_credentials:
                information_flows[id]["stereotype_instances"].append("plaintext_credentials_link")
            information_flows[id]["tagged_values"] = [("Producer Exchange", str(o[0])), ("Routing Key", str(o[1]))]

            # Traceability
            trace = dict()

            trace["item"] = o[2] + " -> " + rabbit_server
            trace["file"] = o[3][0]
            trace["line"] = o[3][1]
            trace["span"] = o[3][2]

            traceability.add_trace(trace)

            # Traceability
            trace = dict()
            trace["parent_item"] = o[2] + " -> " + rabbit_server
            trace["item"] = "message_producer_rabbitmq"
            trace["file"] = o[3][0]
            trace["line"] = o[3][1]
            trace["span"] = o[3][2]

            traceability.add_trace(trace)

    else:
        information_flows_set = set()
        information_flows = dict()
        for o in outgoing_endpoints:
            regex = re.compile(o[1])
            for i in incoming_endpoints:
                if re.search(regex, i[0]):
                    information_flows_set.add((o[2], i[1], o[0], i[0], o[1], i[2], o[3]))
        for i in information_flows_set:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = i[0]
            information_flows[id]["receiver"] = i[1]
            information_flows[id]["exchange"] = i[2]
            information_flows[id]["queue"] = i[3]
            information_flows[id]["stereotype_instances"] = ["message_producer_rabbitmq"]
            information_flows[id]["tagged_values"] = {"Producer Exchange": i[2], "Queue": i[3], "Routing Key": i[4]}

            # Traceability
            trace = dict()
            trace["item"] = str(i[0]) + " -> " + str(i[1])
            trace["file"] = i[4][0]
            trace["line"] = i[4][1]
            trace["span"] = i[4][2]

            traceability.add_trace(trace)

            ## Twice because there are two evidences
            trace["item"] = str(i[0]) + " -> " + str(i[1])
            trace["file"] = i[5][0]
            trace["line"] = i[5][1]
            trace["span"] = i[5][2]

            traceability.add_trace(trace)

    tmp.tmp_config.set("DFD", "microservices", str(microservices))
    return information_flows


def detect_rabbitmq_server(microservices: dict) -> dict:
    """Detects RabbitMQ server.
    """

    raw_files = fi.get_file_as_yaml("docker-compose.yml")
    if len(raw_files) == 0:
        raw_files = fi.get_file_as_yaml("docker-compose.yaml")
    if len(raw_files) == 0:
        raw_files = fi.get_file_as_yaml("docker-compose*")
    if len(raw_files) == 0:
        return microservices
    file = yaml.load(raw_files[0]["content"], Loader = yaml.FullLoader)

    if "services" in file.keys():
        for s in file.get("services"):
            try:
                image = file.get("services", {}).get(s).get("image")
                if "rabbitmq:" in image.split("/")[-1]:
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == s:
                            microservices[m]["stereotype_instances"].append("message_broker")
                            microservices[m]["tagged_values"].append(("Message Broker", "RabbitMQ"))

                            trace = dict()
                            trace["parent_item"] = microservices[m]["servicename"]
                            trace["item"] = "message_broker"
                            trace["file"] = "heuristic, based on image in Docker Compose"
                            trace["line"] = "heuristic, based on image in Docker Compose"
                            trace["span"] = "heuristic, based on image in Docker Compose"
                            traceability.add_trace(trace)

            except:
                pass
            try:
                build = file.get("services", {}).get(s).get("build")
                if "rabbitmq" in build or "rabbit-mq" in build:
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == s:
                            microservices[m]["stereotype_instances"].append("message_broker")
                            microservices[m]["tagged_values"].append(("Message Broker", "RabbitMQ"))

                            trace = dict()
                            trace["parent_item"] = microservices[m]["servicename"]
                            trace["item"] = "message_broker"
                            trace["file"] = "heuristic, based on image in Docker Compose"
                            trace["line"] = "heuristic, based on image in Docker Compose"
                            trace["span"] = "heuristic, based on image in Docker Compose"
                            traceability.add_trace(trace)
            except:
                pass
    else:
        for s in file.keys():
            try:
                image = file.get(s).get("image")
                if "rabbitmq:" in image.split("/")[-1]:
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == s:
                            microservices[m]["stereotype_instances"].append("message_broker")
                            microservices[m]["tagged_values"].append(("Message Broker", "RabbitMQ"))

                            trace = dict()
                            trace["parent_item"] = m
                            trace["item"] = "message_broker"
                            trace["file"] = "heuristic"
                            trace["line"] = "heuristic"
                            trace["span"] = "heuristic"
                            traceability.add_trace(trace)
            except:
                pass
            try:
                build = file.get(s).get("build")
                if "rabbitmq" in build or "rabbit-mq" in build:
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == s:
                            microservices[m]["stereotype_instances"].append("message_broker")
                            microservices[m]["tagged_values"].append(("Message Broker", "RabbitMQ"))

                            trace = dict()
                            trace["parent_item"] = m
                            trace["item"] = "message_broker"
                            trace["file"] = "heuristic"
                            trace["line"] = "heuristic"
                            trace["span"] = "heuristic"
                            traceability.add_trace(trace)
            except:
                pass

    return microservices
