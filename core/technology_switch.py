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

CONTAINER_TECH_LIST = {"Maven": mvn, "Gradle": grd, "DockerCompose": dcm}
COMMUNICATIONS_TECH_LIST = {"RabbitMQ": rmq, "Kafka": kfk, "RestTemplate": rst, "FeignClient": fgn,
                            "Implicit Connections": imp, "Database Connections": dbc, "HTML": html,
                            "Docker-Compose": dcm}


def set_microservices(dfd):
    """Calls set_microservices from correct container technology or returns existing list.
    """

    for func in CONTAINER_TECH_LIST.values():
        func.set_microservices(dfd)


def set_information_flows(dfd) -> dict:
    """Calls get_information_flows from correct communication technology.
    """

    for func in COMMUNICATIONS_TECH_LIST.values():
        func.set_information_flows(dfd)

    return dfd["information_flows"]


def detect_microservice(file_path: str, dfd) -> str:
    """Calls detect_microservices from correct microservice detection technology.
    """

    for func in CONTAINER_TECH_LIST.values():
        microservice = func.detect_microservice(file_path, dfd)
        if microservice:
            return microservice
