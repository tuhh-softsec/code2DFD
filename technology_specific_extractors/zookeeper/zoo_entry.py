import output_generators.traceability as traceability


def detect_zookeeper(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects ZooKeeper config services.
    """

    zookeeper_service = False

    # Service
    for m in microservices.keys():
        if "wurstmeister/zookeeper" in microservices[m]["image"]:
            zookeeper_service = microservices[m]["servicename"]
            try:
                microservices[m]["stereotype_instances"].append("configuration_server")
            except:
                microservices[m]["stereotype_instances"] = ["configuration_server"]
            try:
                microservices[m]["tagged_values"].append(("Configuration Server", "ZooKeeper"))
            except:
                microservices[m]["tagged_values"] = [("Configuration Server", "ZooKeeper")]

        # Link to kafka if existing
    if zookeeper_service:
        kafka_service = False
        for m in microservices.keys():
            for prop in microservices[m]["tagged_values"]:
                if prop == ("Message Broker", "Kafka"):
                    kafka_service = microservices[m]["servicename"]
        if kafka_service:
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = zookeeper_service
            information_flows[id]["receiver"] = kafka_service
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            # check if link in other direction
            to_purge = set()
            for i in information_flows.keys():
                if information_flows[i]["sender"] == kafka_service and information_flows[i]["receiver"] == zookeeper_service:
                    to_purge.add(i)
            for p in to_purge:
                information_flows.pop(p)

    return microservices, information_flows
