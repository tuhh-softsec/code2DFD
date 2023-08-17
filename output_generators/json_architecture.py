import json

import tmp.tmp as tmp



def generate_json_architecture(microservices: dict, information_flows: dict, external_components: dict):
    """Creates JSON file that contains a list of plain information flows, without annotations.
    """

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

    return


def write_to_file(architecture_dict):
    """Writes json architecture to file.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    repo_path = repo_path.replace("/", "--")
    filename = "./output/architecture/" + repo_path + ".json"
    with open(filename, 'w') as architecture_file:
        json.dump(architecture_dict, architecture_file, indent = 4)
    return
