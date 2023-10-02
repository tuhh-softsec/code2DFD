import ast
import re

import yaml

import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability

kafka_server = str()


def set_information_flows(dfd) -> set:
    """Connects incoming endpoints, outgoing endpoints, and routings to information flows
    """

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()


    microservices = tech_sw.get_microservices(dfd)

    incoming_endpoints = get_incoming_endpoints(dfd)
    outgoing_endpoints = get_outgoing_endpoints(dfd)

    new_information_flows = match_incoming_to_outgoing_endpoints(microservices, incoming_endpoints, outgoing_endpoints)

    # merge old and new flows
    for ni in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = new_information_flows[ni]

    information_flows = detect_stream_binders(microservices, information_flows, dfd)

    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))

    return information_flows


def get_incoming_endpoints(dfd) -> set:
    """Finds incoming streams, i.e. instances of KafkaListener
    """

    listening_topics = set()
    files = fi.search_keywords("@KafkaListener")

    for f in files.keys():
        file = files[f]
        if "README" in file["name"]:
            pass
        else:
            for line in range(len(file["content"])):
                if "@KafkaListener" in file["content"][line]:
                    new_listening_topic = file["content"][line].split("topics")[1]
                    if "," in new_listening_topic:
                        new_listening_topic = new_listening_topic.split(",")[0]
                    new_listening_topic = new_listening_topic.strip().strip("=").strip(")").strip()

                    if is_list(new_listening_topic):
                        new_listening_topics = ast.literal_eval(new_listening_topic)
                        for topic in new_listening_topics:
                            new_listening_topic = fi.find_variable(new_listening_topic, f)
                            microservice = tech_sw.detect_microservice(file["path"], dfd)
                            listening_topics.add((new_listening_topic, microservice))
                    else:
                        new_listening_topic = fi.find_variable(new_listening_topic, f)
                        microservice = tech_sw.detect_microservice(file["path"], dfd)

                        span = re.search("@KafkaListener", file["content"][line])
                        trace = (file["name"], line, span)
                        listening_topics.add((new_listening_topic, microservice, trace))

    return listening_topics


def is_list(variable: str) -> bool:
    try:
        var_type = ast.literal_eval(variable)
        if var_type == set or var_type == list or var_type == tuple:
            return True
    except:
        return False


def get_outgoing_endpoints(dfd) -> set:
    """Finds points where messages are sent to exchanges via kafkatemplate.send
    """

    kafkatemplates = fi.find_instances("KafkaTemplate")
    commands = ["send"]
    outgoing_endpoints = set()
    asset = str()
    for template in kafkatemplates:
        for command in commands:
            files = fi.search_keywords(f"{template}.{command}")
            for file in files.keys():
                f = files[file]
                if "README" in f["name"]:
                    pass
                else:
                    microservice = tech_sw.detect_microservice(f["path"], dfd)
                    for line in range(len(f["content"])):
                        if (template + "." + command) in f["content"][line]:    #found correct (starting) line
                            topic = str()

                            # look for semicolon indicating end of command -> ´complete_call´ contains whole command
                            if not ";" in f["content"][line]:
                                complete_call = f["content"][line]
                                found_semicolon = False
                                i = line + 1
                                while not found_semicolon and i < len(f["content"]):
                                    if ";" in f["content"][i]:
                                        found_semicolon = True
                                    complete_call += f["content"][i]
                                    i += 1
                            else:
                                complete_call = f["content"][line]

                            # extract topic
                            topic = complete_call.split(command)[1].strip().strip("(").split(",")[0].strip()
                            topic = fi.find_variable(topic, f)

                            # extract data / asset
                            asset = extract_asset(complete_call, command)
                            if asset_is_input(asset, f, line):
                                asset = "Function input " + asset
                            else:
                                asset = fi.find_variable(asset, f)

                            span = re.search(f"{template}.{command}", f["content"][line])
                            trace = (f["path"], line, span)
                            outgoing_endpoints.add((topic, microservice, asset, trace))

    return outgoing_endpoints


def extract_asset(kafkatemplate_call: str, command: str) -> str:
    """Takes a code line that sends via KafkaTemplate and extracts the asset.
    """

    asset = str()

    if command == "send":
        arguments = kafkatemplate_call.split("send")[1].split(";")[0].strip()[1:-1].split(",")
        if len(arguments) > 1:
            asset = arguments[-1]

    return asset


def asset_is_input(variable: str, file, line_nr: int) -> bool:
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


def match_incoming_to_outgoing_endpoints(microservices: dict, incoming_endpoints: set, outgoing_endpoints: set) -> dict:
    """Finds information flows by regexing routing keys of outgoing endpoints to queues of incoming endpoints.
    """
    # incoming: (topic, microservice, (file, line, span))
    # outgoing: (topic, microservice, asset, (file, line, span))

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        information_flows = ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        information_flows = dict()

    kafka_server = False
    for id in microservices.keys():
        if ("Message Broker", "Kafka") in microservices[id]["tagged_values"]:
            kafka_server = microservices[id]["servicename"]

    if kafka_server:
        for i in incoming_endpoints:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = kafka_server
            information_flows[id]["receiver"] = i[1]
            information_flows[id]["stereotype_instances"] = ["message_consumer_kafka", "restful_http"]
            information_flows[id]["tagged_values"] = [("Consumer Topic", str(i[0]))]

            # Traceability
            trace = dict()
            trace["item"] = str(kafka_server) + " -> " + str(i[1])
            trace["file"] = i[2][0]
            trace["line"] = i[2][1]
            trace["span"] = i[2][2]

            traceability.add_trace(trace)

            trace = dict()
            trace["parent_item"] = str(kafka_server) + " -> " + str(i[1])
            trace["item"] = "message_consumer_kafka"
            trace["file"] = i[2][0]
            trace["line"] = i[2][1]
            trace["span"] = i[2][2]

            traceability.add_trace(trace)

        for o in outgoing_endpoints:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = o[1]
            information_flows[id]["receiver"] = kafka_server
            information_flows[id]["stereotype_instances"] = ["message_producer_kafka", "restful_http"]
            information_flows[id]["tagged_values"] = [("Producer Topic", str(o[0]))]

            # Traceability
            trace = dict()

            trace["item"] = str(o[1]) + " -> " + str(kafka_server)
            trace["file"] = o[3][0]
            trace["line"] = o[3][1]
            trace["span"] = o[3][2]

            traceability.add_trace(trace)

            trace = dict()
            trace["parent_item"] = str(o[1]) + " -> " + str(kafka_server)
            trace["item"] = "message_producer_kafka"
            trace["file"] = o[3][0]
            trace["line"] = o[3][1]
            trace["span"] = o[3][2]

            traceability.add_trace(trace)

    else:
        information_flows_set = set()
        for i in incoming_endpoints:

            regex = re.compile(i[0])
            for o in outgoing_endpoints:
                if re.search(regex, o[0]):
                    information_flows_set.add((o[1], i[1], i[0], o[2], i[2], o[3]))

        # this next block is because i don't know if one can put regex as topic when sending as well. Since it's a set, this doesn't hurt
        for o in outgoing_endpoints:
            regex = re.compile(o[0])
            for i in incoming_endpoints:
                if re.search(regex, i[0]):
                    information_flows_set.add((o[1], i[1], i[0], o[2], i[2], o[3]))

        # turn it into a dictionary
        for i in information_flows_set:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()

            information_flows[id]["sender"] = i[0]
            information_flows[id]["receiver"] = i[1]
            information_flows[id]["topic"] = i[2]
            information_flows[id]["asset"] = i[3]

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

    return information_flows


def detect_kafka_server(microservices: dict) -> dict:
    """Detects and marks kafka server.
    """

    global kafka_server

    raw_files = fi.get_file_as_yaml("docker-compose.yml")
    if len(raw_files) == 0:
        raw_files = fi.get_file_as_yaml("docker-compose.yaml")
    if len(raw_files) == 0:
        raw_files = fi.get_file_as_yaml("docker-compose*")
    if len(raw_files) == 0:
        return microservices
    file = yaml.load(raw_files[0]["content"], Loader = yaml.FullLoader)

    if "services" in file:
        for s in file.get("services"):
            try:
                image = file.get("services", {}).get(s).get("image")
                if "kafka" in image.split("/")[-1].casefold():
                    for id in microservices.keys():
                        if microservices[id]["servicename"] == s:
                            kafka_server = microservices[id]["servicename"]
                            try:
                                microservices[id]["stereotype_instances"].append("message_broker")
                            except:
                                microservices[id]["stereotype_instances"] = ["message_broker"]
                            try:
                                microservices[id]["tagged_values"].append(("Message Broker", "Kafka"))
                            except:
                                microservices[id]["tagged_values"] = [("Message Broker", "Kafka")]

                            trace = dict()
                            trace["parent_item"] = microservices[id]["servicename"]
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
                if "kafka" in image.split("/")[-1].casefold():
                    for id in microservices.keys():
                        if microservices[id]["servicename"] == s:
                            kafka_server = microservices[id]["servicename"]
                            try:
                                microservices[id]["stereotype_instances"].append("message_broker")
                            except:
                                microservices[id]["stereotype_instances"] = ["message_broker"]
                            try:
                                microservices[id]["tagged_values"].append(("Message Broker", "Kafka"))
                            except:
                                microservices[id]["tagged_values"] = [("Message Broker", "Kafka")]

                            trace = dict()
                            trace["parent_item"] = microservices[id]["servicename"]
                            trace["item"] = "message_broker"
                            trace["file"] = "heuristic, based on image in Docker Compose"
                            trace["line"] = "heuristic, based on image in Docker Compose"
                            trace["span"] = "heuristic, based on image in Docker Compose"

                            traceability.add_trace(trace)
            except:
                pass
    return microservices


def detect_stream_binders(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects connections to kafka via stream bindings.
    """

    global kafka_server

    for m in microservices.keys():
        connected = False
        out_topic = False
        in_topic = False

        for prop in microservices[m]["properties"]:
            if prop[0] == "kafka_stream_binder" and prop[1] == kafka_server:
                connected = True
            elif prop[0] == "kafka_stream_topic_out":
                out_topic = prop[1]
            elif prop[0] == "kafka_stream_topic_in":
                in_topic = prop[1]

        if connected:
            # Outgoing
            results = fi.search_keywords("@SendTo")
            for r in results.keys():
                if tech_sw.detect_microservice(results[r]["path"], dfd) == microservices[m]["servicename"]:
                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()

                    information_flows[id]["sender"] = microservices[m]["servicename"]
                    information_flows[id]["receiver"] = kafka_server
                    information_flows[id]["stereotype_instances"] = ["message_producer_kafka", "restful_http"]
                    if out_topic:
                        information_flows[id]["tagged_values"] = {("Producer Topic", out_topic)}

                    # Traceability
                    trace = dict()
                    trace["item"] = str(microservices[m]["servicename"]) + " -> " + str(kafka_server)
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)

                    trace = dict()
                    trace["parent_item"] = str(microservices[m]["servicename"]) + " -> " + str(kafka_server)
                    trace["item"] = "message_producer_kafka"
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)

            # Incoming
            results = fi.search_keywords("@StreamListener")
            for r in results.keys():
                if tech_sw.detect_microservice(results[r]["path"], dfd) == microservices[m]["servicename"]:

                    try:
                        id = max(information_flows.keys()) + 1
                    except:
                        id = 0
                    information_flows[id] = dict()

                    information_flows[id]["sender"] = kafka_server
                    information_flows[id]["receiver"] = microservices[m]["servicename"]
                    information_flows[id]["stereotype_instances"] = ["message_consumer_kafka", "restful_http"]
                    if in_topic:
                        information_flows[id]["tagged_values"] = {("Consumer Topic", in_topic)}

                    # Traceability
                    trace = dict()
                    trace["item"] = str(kafka_server) + " -> " + str(microservices[m]["servicename"])
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)

                    trace = dict()
                    trace["parent_item"] = str(kafka_server) + " -> " + str(microservices[m]["servicename"])
                    trace["item"] = "message_consumer_kafka"
                    trace["file"] = results[r]["path"]
                    trace["line"] = results[r]["line_nr"]
                    trace["span"] = results[r]["span"]

                    traceability.add_trace(trace)


    return information_flows
