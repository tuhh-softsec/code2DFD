from core.Service import CService
from core.ExternalEntity import CExternalEntity
from core.InformationFlow import CInformationFlow

import core.technology_switch as tech_sw
import importlib


class CDFD:
    """Class CDFD as central collection of all extracted information.
    """

    def __init__(self, name, repo_path):
        self.name = name
        self.repo_path = repo_path
        self.services = list()
        self.external_entities = list()
        self.information_flows = list()
        self.traceability = dict()

    def __str__(self):
        return f"DFD {self.name}"
    
    def print_all(self):
        self.print_services()
        self.print_information_flows()
        self.print_external_entities()

    def print_services(self):
        for s in self.services:
            print(s)

    def print_information_flows(self):
        for i in self.information_flows:
            print(i)

    def print_external_entities(self):
        for e in self.external_entities:
            print(e)

    def add_service(self, service: CService):
        if not service.name in [s.name for s in self.services]:
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

        # list of all extractors
        with open(extractors_file_path, 'r') as file:
            extractors = file.readlines()

        # dynamically import extractors 
        for extractor in extractors:
            module = importlib.import_module(f"technology_specific_extractors.{extractor}.{extractor}")
            # get the main method
            ex = getattr(module, f"detect_{extractor}")
            # execute main method, save returned services, flows, and external entities
            ex(self)
            # now full dfd object is passed to extractors and the merging logic is done there.
            # more burden for adding new ones, but probably best


    def extract_services(self):
        microservices = tech_sw.get_microservices(self)
        for m in microservices:
            self.add_service(microservices[m])
        
    def print_test(self):
        print("testtesttesttesttest")