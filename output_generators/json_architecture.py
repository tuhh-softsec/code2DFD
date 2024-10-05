import json
import os

import tmp.tmp as tmp


def generate_json_architecture(microservices: dict, information_flows: dict, external_components: dict):
    """Creates JSON file that contains the complete extracted architecture.
    """

    full_dict = {"microservices": list(microservices.values()),
                 "information_flows": list(information_flows.values()),
                 "external_components": list(external_components.values())}
    
    repo_path = tmp.tmp_config["Repository"]["path"]
    repo_path = repo_path.replace("/", "--")
    filename = "./output/json_architecture/" + repo_path + ".json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as architecture_file:
        json.dump(full_dict, architecture_file, indent=4)
