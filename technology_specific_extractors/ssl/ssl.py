
from core.DFD import CDFD
from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow

def detect_ssl(dfd: CDFD) -> dict:
    """Checks if services have ssl enabled.
    """

    for service in dfd.services:
        for prop in service.properties:
            if prop[0] == "ssl_enabled":
                if not bool(prop[1]):
                    service.stereotypes.append("ssl_disabled")
                elif bool(prop[1]):
                    service.stereotypes.append("ssl_enabled")
            elif prop[0] == "ssl_protocol":
                service.tagged_values.append(("SSL Protocol", prop[1]))
    return 
