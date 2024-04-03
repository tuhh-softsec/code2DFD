import core.file_interaction as fi
import output_generators.traceability as traceability

from core.DFD import CDFD
from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow


def detect_databases(dfd: CDFD) -> dict:
    """Detects databases.
    """

    for service in dfd.services:
        database = False
        if "image" in service.properties:   # TODO: images are not recorded atm. Add in initial detection extractors
            if "mongo:" in service.properties:  # TODO: these need to be adapted to properties type then
                database = "MongoDB"
            elif "mysql-server:" in service.properties:
                database = "MySQL"

        if database:
            service.stereotypes.append("database")
            service.tagged_values.append(("Database", database))

        else:
            detect_via_docker(dfd, service)

    return


def detect_via_docker(dfd: CDFD, service: CService):
    """Checks microservifces' build paths for dockerfile. If found, parses for possible databases.
    """

    # path = service.properties
    # dockerfile_lines = fi.check_dockerfile(path)

    # database = False
    # if dockerfile_lines:
    #     for line in dockerfile_lines:
    #         if "FROM" in line:
    #             if "mongo" in line:
    #                 database = "MongoDB"
    #             elif "postgres" in line:
    #                 database = "PostgreSQL"
    # if database:
    #     service.stereotypes.append("database")
    #     service.tagged_values.append(("Database", database))

    return 
