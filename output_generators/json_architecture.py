import json
import os
from pathlib import Path

import tmp.tmp as tmp


def generate_json_architecture(microservices: dict, information_flows: dict, external_components: dict):
    """Creates JSON file that contains the complete extracted architecture.
    """

    full_dict = {"microservices": list(microservices.values()),
                 "information_flows": list(information_flows.values()),
                 "external_components": list(external_components.values())}
    
    output_path = tmp.tmp_config["Analysis Settings"]["output_path"]
    parts = Path(output_path).parts
    filename = f"{parts[-2]}--{parts[-1]}_json_architecture.json"
    output_path = os.path.join(output_path, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as architecture_file:
        json.dump(full_dict, architecture_file, indent=4)
