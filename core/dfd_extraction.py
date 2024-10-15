import ast
import os
from datetime import datetime
from itertools import combinations

import output_generators.codeable_model as codeable_model
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.json_architecture as json_architecture
import output_generators.json_edges as json_edges
import output_generators.traceability as traceability
import output_generators.visualizer as visualizer
from technology_specific_extractors.apache_httpd.aph_entry import detect_apachehttpd_webserver
from technology_specific_extractors.circuit_breaker.cbr_entry import detect_circuit_breakers
from technology_specific_extractors.consul.cns_entry import detect_consul
from technology_specific_extractors.database_connections.dbc_entry import clean_database_connections
from technology_specific_extractors.databases.dbs_entry import detect_databases
from technology_specific_extractors.elasticsearch.ela_entry import detect_elasticsearch
from technology_specific_extractors.eureka.eur_entry import detect_eureka, detect_eureka_server_only
from technology_specific_extractors.grafana.grf_entry import detect_grafana
from technology_specific_extractors.http_security.hts_entry import detect_authentication_scopes
from technology_specific_extractors.hystrix.hsx_entry import (detect_hystrix_circuit_breakers,
                                     detect_hystrix_dashboard)
from technology_specific_extractors.kafka.kfk_entry import detect_kafka_server
from technology_specific_extractors.kibana.kib_entry import detect_kibana
from technology_specific_extractors.load_balancer.lob_entry import detect_load_balancers
from technology_specific_extractors.local_logging.llo_entry import detect_local_logging
from technology_specific_extractors.logstash.log_entry import detect_logstash
from technology_specific_extractors.nginx.ngn_entry import detect_nginx
from technology_specific_extractors.plaintext_credentials.plc_entry import set_plaintext_credentials
from technology_specific_extractors.prometheus.prm_entry import detect_prometheus_server
from technology_specific_extractors.rabbitmq.rmq_entry import detect_rabbitmq_server
from technology_specific_extractors.repository_rest_resource.rrr_entry import detect_endpoints
from technology_specific_extractors.ribbon.rib_entry import detect_ribbon_load_balancers
from technology_specific_extractors.service_functionality_classification.itf_entry import \
    classify_internal_infrastructural
from technology_specific_extractors.spring_admin.sad_entry import detect_spring_admin_server
from technology_specific_extractors.spring_config.cnf_entry import detect_spring_config
from technology_specific_extractors.spring_encryption.enc_entry import detect_spring_encryption
from technology_specific_extractors.spring_gateway.sgt_entry import detect_spring_cloud_gateway
from technology_specific_extractors.spring_oauth.soa_entry import detect_spring_oauth
from technology_specific_extractors.ssl.ssl_entry import detect_ssl_services
from technology_specific_extractors.turbine.trb_entry import detect_turbine
from technology_specific_extractors.zipkin.zip_entry import detect_zipkin_server
from technology_specific_extractors.zookeeper.zoo_entry import detect_zookeeper
from technology_specific_extractors.zuul.zul_entry import detect_zuul

from core.DFD import CDFD


def perform_analysis():
    """Main function for the extraction, calling all technology-specific extractors, managing output etc.
    """

    dfd = CDFD("TestDFD")
    repo_path = tmp.tmp_config["Repository"]["path"]
    now = datetime.now()
    start_time = now.strftime("%H:%M:%S")
    print("\n\tStart extraction of DFD for " + repo_path + " at " + str(start_time))

    microservices, information_flows, external_components = dict(), dict(), dict()

    microservices = tech_sw.get_microservices(dfd)
    
    microservices = detect_databases(microservices)
    microservices = overwrite_port(microservices)
    microservices = detect_ssl_services(microservices)
    print("Extracted services from build- and IaC-files")

    # Parse internal and external configuration files
    microservices, information_flows, external_components = detect_spring_config(microservices, information_flows, external_components, dfd)
    microservices = detect_eureka_server_only(microservices, dfd)
    microservices = overwrite_port(microservices)

    # Classify brokers (needed for information flows)
    microservices = classify_brokers(microservices)

    # Check authentication information of services
    microservices = detect_authentication_scopes(microservices, dfd)
    tmp.tmp_config.set("DFD", "microservices", str(microservices))

    # Get information flows
    tmp.tmp_config.set("DFD", "external_components", str(external_components))

    new_information_flows = tech_sw.get_information_flows(dfd)
    external_components = ast.literal_eval(tmp.tmp_config["DFD"]["external_components"])

    # Merge old and new
    for new_flow in new_information_flows.keys():
        try:
            id = max(information_flows.keys()) + 1
        except:
            id = 0
        information_flows[id] = dict()
        information_flows[id] = new_information_flows[new_flow]
    print("Extracted information flows from API-calls, message brokers, and database connections")

    # Detect everything else / execute all technology implementations
    microservices = tech_sw.get_microservices(dfd)
    microservices, information_flows, external_components = classify_microservices(microservices, information_flows, external_components, dfd)

    # Merging
    print("Merging duplicate items")

    merge_duplicate_flows(information_flows)

    merge_duplicate_nodes(microservices)
    merge_duplicate_nodes(external_components)

    merge_duplicate_annotations(microservices)
    merge_duplicate_annotations(information_flows)
    merge_duplicate_annotations(external_components)

    print("Cleaning database connections")

    clean_database_connections(microservices, information_flows)

    # Printing
    print("\nFinished extraction")
    repo_path = repo_path.replace("/", "_")
    filename = "./output/results/" + repo_path + ".txt"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as output_file:
        if information_flows:
            output_file.write("\nInformation Flows:\n")
            for i in information_flows.keys():
                output_file.write("\n" + str(information_flows[i]))

        if microservices:
            output_file.write("\nMicroservices:\n")
            for m in microservices.keys():
                microservices[m].pop("image", None)
                microservices[m].pop("pom_path", None)
                microservices[m].pop("properties", None)
                output_file.write("\n" + str(microservices[m]))

        if external_components:
            output_file.write("\nExternal Components:\n")
            for e in external_components.keys():
                output_file.write("\n" + str(external_components[e]))

    # Writing dict for calculating metrics
    filename_dict = "./output/results/" + repo_path + "_dict.txt"
    os.makedirs(os.path.dirname(filename_dict), exist_ok=True)
    with open(filename_dict, "w") as output_file_dict:
        complete = dict()
        complete["microservices"] = microservices
        complete["information_flows"] = information_flows
        complete["external_components"] = external_components

        output_file_dict.write(str(complete))

    # Saving
    tmp.tmp_config.set("DFD", "microservices", str(microservices))
    tmp.tmp_config.set("DFD", "information_flows", str(information_flows))
    tmp.tmp_config.set("DFD", "external_components", str(external_components))

    codeable_models, codeable_models_path = codeable_model.output_codeable_model(microservices, information_flows, external_components)
    traceability_content = traceability.output_traceability()
    visualizer.output_png(codeable_models_path)
    json_edges.generate_json_edges(information_flows)
    json_architecture.generate_json_architecture(microservices, information_flows, external_components)

    #calculate_metrics.calculate_single_system(repo_path)

    #check_traceability.check_traceability(microservices, information_flows, external_components, traceability_content)

    return codeable_models, traceability_content


def classify_brokers(microservices: dict) -> dict:
    """Classifies kafka and rabbitmq servers, because they are needed for the information flows.
    """

    microservices = detect_rabbitmq_server(microservices)
    microservices = detect_kafka_server(microservices)
    tmp.tmp_config.set("DFD", "microservices", str(microservices))
    return microservices


def classify_microservices(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Tries to determine the microservice's funcitonality.
    """

    print("Classifying all services")
    microservices, information_flows = detect_eureka(microservices, information_flows, dfd)
    microservices, information_flows, external_components = detect_zuul(microservices, information_flows, external_components, dfd)
    microservices, information_flows, external_components = detect_spring_cloud_gateway(microservices, information_flows, external_components, dfd)
    microservices, information_flows = detect_spring_oauth(microservices, information_flows, dfd)
    microservices, information_flows = detect_consul(microservices, information_flows, dfd)
    microservices, information_flows = detect_hystrix_dashboard(microservices, information_flows, dfd)
    microservices, information_flows = detect_turbine(microservices, information_flows, dfd)
    microservices, information_flows = detect_local_logging(microservices, information_flows, dfd)
    microservices, information_flows = detect_zipkin_server(microservices, information_flows, dfd)
    microservices, information_flows = detect_spring_admin_server(microservices, information_flows, dfd)
    microservices, information_flows = detect_prometheus_server(microservices, information_flows, dfd)
    microservices, information_flows = detect_circuit_breakers(microservices, information_flows, dfd)
    microservices, information_flows = detect_load_balancers(microservices, information_flows, dfd)
    microservices, information_flows = detect_ribbon_load_balancers(microservices, information_flows, dfd)
    microservices, information_flows = detect_hystrix_circuit_breakers(microservices, information_flows, dfd)
    microservices, information_flows = detect_zookeeper(microservices, information_flows, dfd)
    microservices, information_flows = detect_kibana(microservices, information_flows, dfd)
    microservices, information_flows = detect_elasticsearch(microservices, information_flows, dfd)
    microservices, information_flows, external_components = detect_logstash(microservices, information_flows, external_components, dfd)
    microservices, information_flows, external_components = detect_nginx(microservices, information_flows, external_components, dfd)
    microservices, information_flows = detect_grafana(microservices, information_flows, dfd)
    microservices, information_flows = detect_spring_encryption(microservices, information_flows, dfd)
    microservices = detect_endpoints(microservices, dfd)

    microservices, information_flows, external_components = detect_miscellaneous(microservices, information_flows, external_components)
    microservices, information_flows, external_components = detect_apachehttpd_webserver(microservices, information_flows, external_components, dfd)
    microservices = classify_internal_infrastructural(microservices)
    microservices = set_plaintext_credentials(microservices)

    return microservices, information_flows, external_components


def overwrite_port(microservices: dict) -> dict:
    """Writes port from properties to tagged vallues.
    """

    for m in microservices.keys():
        port = False
        for prop in microservices[m]["properties"]:
            if prop[0] == "port":
                if type(prop[1]) == str:
                    if "port" in prop[1].casefold():
                        port = prop[1].split(":")[1].strip("}")
                    else:
                        port = int(prop[1].strip())
                else:
                    port = prop[1]
                if port:
                    # Traceability
                    trace = dict()
                    trace["parent_item"] = microservices[m]["name"]
                    trace["item"] = "Port"
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)
                    if "tagged_values" in microservices[m]:
                        microservices[m]["tagged_values"].append(("Port", port))
                    else:
                        microservices[m]["tagged_values"] = [("Port", port)]

    return microservices


def detect_miscellaneous(microservices: dict, information_flows: dict, external_components: dict) -> dict:
    """Goes through properties extracted for each service to check for some things that don't fit anywhere else (mail servers, external websites, etc.).
    """

    for m in microservices.keys():
        if "properties" in microservices[m].keys():
            for prop in microservices[m]["properties"]:

                # external mail server
                if prop[0] == "mail_host":
                    mail_username, mail_password = False, False
                    for prop2 in microservices[m]["properties"]:
                        if prop2[0] == "mail_password":
                            mail_password = prop2[1]
                        elif prop2[0] == "mail_username":
                            mail_username = prop2[1]
                    # create external mail server
                    try:
                        id = max(external_components.keys()) + 1
                    except:
                        id = 0
                    external_components[id] = dict()
                    external_components[id]["name"] = "mail-server"
                    external_components[id]["stereotype_instances"] = ["mail_server", "entrypoint", "exitpoint"]
                    external_components[id]["tagged_values"] = [("Host", prop[1])]
                    if mail_password:
                        external_components[id]["tagged_values"].append(("Password", mail_password))
                        external_components[id]["stereotype_instances"].append("plaintext_credentials")
                    if mail_username:
                        external_components[id]["tagged_values"].append(("Username", mail_username))

                    trace = dict()
                    trace["item"] = "mail-server"
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)

                    trace["parent_item"] = "mail-server"
                    trace["item"] = "entrypoint"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    trace["parent_item"] = "mail-server"
                    trace["item"] = "exitpoint"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    trace["parent_item"] = "mail-server"
                    trace["item"] = "mail_server"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    # create connection
                    try:
                        id2 = max(information_flows.keys()) + 1
                    except:
                        id2 = 0
                    information_flows[id2] = dict()
                    information_flows[id2]["sender"] = microservices[m]["name"]
                    information_flows[id2]["receiver"] = "mail-server"
                    information_flows[id2]["stereotype_instances"] = ["restful_http"]
                    if mail_password:
                        information_flows[id2]["stereotype_instances"].append("plaintext_credentials_link")

                    trace = dict()
                    trace["item"] = microservices[m]["name"] + " -> mail-server"
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)

                # external api rate website
                elif prop[0] == "rates_url":
                    # create external component
                    try:
                        id = max(external_components.keys()) + 1
                    except:
                        id = 0
                    external_components[id] = dict()
                    external_components[id]["name"] = "external-website"
                    external_components[id]["stereotype_instances"] = ["external_website", "entrypoint", "exitpoint"]
                    external_components[id]["tagged_values"] = [("URL", prop[1])]

                    trace = dict()
                    trace["item"] = "external-website"
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)

                    trace["parent_item"] = "external-website"
                    trace["item"] = "entrypoint"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    trace["parent_item"] = "external-website"
                    trace["item"] = "exitpoint"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    trace["parent_item"] = "external-website"
                    trace["item"] = "external_website"
                    trace["file"] = "heuristic"
                    trace["line"] = "heuristic"
                    trace["span"] = "heuristic"

                    traceability.add_trace(trace)

                    # create connection
                    try:
                        id2 = max(information_flows.keys()) + 1
                    except:
                        id2 = 0
                    information_flows[id2] = dict()
                    information_flows[id2]["sender"] = "external-website"
                    information_flows[id2]["receiver"] = microservices[m]["name"]
                    information_flows[id2]["stereotype_instances"] = ["restful_http"]

                    trace = dict()
                    trace["item"] = "external-website -> " + microservices[m]["name"]
                    trace["file"] = prop[2][0]
                    trace["line"] = prop[2][1]
                    trace["span"] = prop[2][2]

                    traceability.add_trace(trace)

                # connection config to services
                elif prop[0] == "config_connected":
                    for m2 in microservices.keys():
                        for stereotype in microservices[m2]["stereotype_instances"]:
                            if stereotype == "configuration_server":
                                try:
                                    id = max(information_flows.keys()) + 1
                                except:
                                    id = 0
                                information_flows[id] = dict()
                                information_flows[id]["sender"] = microservices[m2]["name"]
                                information_flows[id]["receiver"] = microservices[m]["name"]
                                information_flows[id]["stereotype_instances"] = ["restful_http"]

                                trace = dict()
                                trace["item"] = microservices[m2]["name"] + " -> " + microservices[m]["name"]
                                trace["file"] = prop[2][0]
                                trace["line"] = prop[2][1]
                                trace["span"] = prop[2][2]

                                traceability.add_trace(trace)
    return microservices, information_flows, external_components


def merge_duplicate_flows(information_flows: dict):
    """Multiple flows with the same sender and receiver might occur. They are merged here.
    """

    to_delete = set()
    for i, j in combinations(information_flows.keys(), 2):
        flow_i = information_flows[i]
        flow_i["sender"] = flow_i["sender"].casefold()
        flow_i["receiver"] = flow_i["receiver"].casefold()
        if i == j:
            continue
        flow_j = information_flows[j]
        flow_j["sender"] = flow_j["sender"].casefold()
        flow_j["receiver"] = flow_j["receiver"].casefold()

        if flow_i["sender"] == flow_j["sender"] and flow_i["receiver"] == flow_j["receiver"]:
            # merge
            for field, j_value in flow_j.items():
                if field not in ["sender", "receiver"]:
                    flow_i[field] = flow_i.get(field, list()) + list(j_value)
            to_delete.add(j)
    for k in to_delete:
        del information_flows[k]


def merge_duplicate_nodes(nodes: dict):
    """Merge duplicate nodes
    """

    # Microservices
    to_delete = set()
    for i, j in combinations(nodes.keys(), 2):
        node_i = nodes[i]
        node_i["name"] = node_i["name"].casefold()
        if i == j:
            continue
        node_j = nodes[j]
        node_j["name"] = node_j["name"].casefold()

        if node_i["name"] == node_j["name"]:
            # merge
            for field, j_value in node_j.items():
                if field not in ["name", "type"]:
                    node_i[field] = node_i.get(field, list()) + list(j_value)
            to_delete.add(j)
    for k in to_delete:
        del nodes[k]


def merge_duplicate_annotations(collection: dict):
    """Merge annotations of all items
    """

    for item in collection.values():
        if "stereotype_instances" in item:
            item["stereotype_instances"] = list(set(item["stereotype_instances"]))

        if "tagged_values" in item:
            tagged_values_set = set()
            for tag, tagged_value in item["tagged_values"]:
                if tag == "Port":
                    if isinstance(tagged_value, str):
                        tagged_value = tagged_value.split("/")[0]  # Could be a protocol like 3306/tcp
                    if not isinstance(tagged_value, int):
                        try:
                            tagged_value = int(tagged_value)
                        except ValueError:
                            pass
                elif isinstance(tagged_value, list):
                    tagged_value = str(tagged_value)
                tagged_values_set.add((tag, tagged_value))
            item["tagged_values"] = list(tagged_values_set)
