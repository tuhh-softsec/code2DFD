import json
import os
from pathlib import Path

from core.config import code2dfd_config


def generate_json_architecture(dfd):
    """Creates JSON file that contains the complete extracted architecture.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]
    external_components = dfd["external_components"]

    full_dict = {"microservices": list(microservices.values()),
                 "information_flows": list(information_flows.values()),
                 "external_components": list(external_components.values())}
    
    output_path = code2dfd_config["Analysis Settings"]["output_path"]
    parts = Path(output_path).parts
    filename = f"{parts[-2]}--{parts[-1]}_json_architecture.json"
    output_path = os.path.join(output_path, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as architecture_file:
        json.dump(full_dict, architecture_file, indent=4)
