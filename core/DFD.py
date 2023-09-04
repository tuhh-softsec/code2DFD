from core.service import CService
from core.external_entity import CExternalEntity
from core.information_flow import CInformationFlow


class CDFD:
    """Class CDFD as central collection of all extracted information.
    """

    def __init__(self, name):
        self.name = name
        self.services = [CService]
        #self.external_entities = list(CExternalEntity)
        #self.information_flows = list(CInformationFlow)
        self.traceability = dict()
        print("Initialization")

    def __str__(self):
        return f"DFD {self.name}"

    def add_service(self, service):
        self.services.append(service)
        pass

    def add_external_entity(self, external_entity):
        pass

    def add_information_flow(self, information_flow):
        pass

    def create_png(self):
        pass
    
    def create_json(self):
        pass

    def add_traceability(self, model_item, item_type, file, line):
        pass