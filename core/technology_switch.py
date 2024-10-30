import ast

from output_generators.logger import logger
import technology_specific_extractors.database_connections.dbc_entry as dbc
import technology_specific_extractors.docker_compose.dcm_entry as dcm
import technology_specific_extractors.feign_client.fgn_entry as fgn
import technology_specific_extractors.gradle.grd_entry as grd
import technology_specific_extractors.html.html_entry as html
import technology_specific_extractors.implicit_connections.imp_entry as imp
import technology_specific_extractors.kafka.kfk_entry as kfk
import technology_specific_extractors.maven.mvn_entry as mvn
import technology_specific_extractors.rabbitmq.rmq_entry as rmq
import technology_specific_extractors.resttemplate.rst_entry as rst
import tmp.tmp as tmp

COMMUNICATIONS_TECH_LIST = {"RabbitMQ": rmq, "Kafka": kfk, "RestTemplate": rst, "FeignClient": fgn,
                            "Implicit Connections": imp, "Database Connections": dbc, "HTML": html,
                            "Docker-Compose": dcm}


def get_microservices(dfd) -> dict:
    """Calls get_microservices from correct container technology or returns existing list.
    """

    if tmp.tmp_config.has_option("DFD", "microservices"):
        return ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])
    else:
        logger.info("Microservices not set yet, start extraction")

        mvn.set_microservices(dfd)
        grd.set_microservices(dfd)
        dcm.set_microservices(dfd)
        if tmp.tmp_config.has_option("DFD", "microservices"):
            return ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])


def get_information_flows(dfd) -> dict:
    """Calls get_information_flows from correct communication technology.
    """

    if tmp.tmp_config.has_option("DFD", "information_flows"):
        return ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])
    else:
        logger.info("Information flows not set yet, start extraction")
        for func in COMMUNICATIONS_TECH_LIST.values():
            func.set_information_flows(dfd)

        if tmp.tmp_config.has_option("DFD", "information_flows"):
            return ast.literal_eval(tmp.tmp_config["DFD"]["information_flows"])


def detect_microservice(file_path: str, dfd) -> str:
    """Calls detect_microservices from correct microservice detection technology.
    """

    microservice = mvn.detect_microservice(file_path, dfd)
    if not microservice:
        microservice = grd.detect_microservice(file_path, dfd)
    if not microservice:
        microservice = dcm.detect_microservice(file_path, dfd)
    return microservice
