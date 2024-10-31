"""NOTE: this does not generate the complete output as JSON file. It only saves the information flows into /edges.
This was needed for another project using Code2DFD and will remain here for now until removed in the future.
"""


import json
import os
from pathlib import Path

from core.config import code2dfd_config


def generate_json_edges(dfd: dict):
    """Creates JSON file that contains a list of plain information flows, without annotations.
    """
    information_flows = dfd["information_flows"]

    edges_list = list()
    for i in information_flows.keys():
        sender = information_flows[i]["sender"]
        receiver = information_flows[i]["receiver"]
        # add flow
        new_edge = dict()
        new_edge["sender"] = sender
        new_edge["receiver"] = receiver
        edges_list.append(new_edge)

    architecture_dict = dict()
    architecture_dict["edges"] = edges_list
    write_to_file(architecture_dict)


def write_to_file(architecture_dict):
    """Writes json architecture to file.
    """

    output_path = code2dfd_config["Analysis Settings"]["output_path"]
    parts = Path(output_path).parts
    filename = f"{parts[-2]}--{parts[-1]}_edges.json"
    output_path = os.path.join(output_path, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as architecture_file:
        json.dump(architecture_dict, architecture_file, indent=4)
