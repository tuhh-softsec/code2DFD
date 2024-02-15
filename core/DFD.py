from core.service import CService
from core.external_entity import CExternalEntity
from core.information_flow import CInformationFlow


class CDFD:
    """Class CDFD as central collection of all extracted information.
    """

    def __init__(self, name):
        self.name = name
        self.services = [CService]
        self.external_entities = [CExternalEntity]
        self.information_flows = [CInformationFlow]
        self.traceability = dict()

    def __str__(self):
        return f"DFD {self.name}"

    def add_service(self, service: CService):
        if not service.name in [s.name for s in self.services]:
            self.services.append(service)
        else:
            # merge stereotypes
            pass
        

    def add_external_entity(self, external_entity):
        if not external_entity.name in [e.name for e in self.external_entities]:
            self.external_entities.append(external_entity)
        else:
            # merge stereotypes
            pass

    def add_information_flow(self, information_flow):
        if not information_flow.name in [i.name for i in self.information_flows]:
            self.information_flows.append(information_flow)
        else:
            # merge stereotypes
            pass

    def create_png(self):
        pass
    
    def create_json(self):
        pass

    def add_traceability(self, model_item, item_type, file, line):
        pass