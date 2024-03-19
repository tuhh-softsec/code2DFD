from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow

import core.technology_switch as tech_sw


class CDFD:
    """Class CDFD as central collection of all extracted information.
    """

    def __init__(self, name):
        self.name = name
        self.services = list()
        self.external_entities = list()
        self.information_flows = list()
        self.traceability = dict()

    def __str__(self):
        return f"DFD {self.name}"
    
    def print_services(self):

        print("######")
        for s in self.services:
            print(self.services)
        print("######")
        

    def add_service(self, service: CService):
        #if not service.name in [s.name for s in self.services]:
        self.services.append(service)
        #else:
            # merge stereotypes
        #    pass
        
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

    def run_technology_specific_extractors(self, extractors_file_path):
        # open file containing list of extractors
        # dynamically import the extractor
        # execute extractor (imports to all have to be all model items for standardization)
        # adjust self. model items to output from each extractor

        
        with open(extractors_file_path, 'r') as file:
            extractors = file.readlines()

        
        for extractor in extractors:
            module = __import__(extractor)
            ex = getattr(module, extractor)


    def extract_services(self):
        microservices = tech_sw.get_microservices(self)
        for m in microservices:
            self.add_service(microservices[m])
        