import ast
import json

import tmp.tmp as tmp

traceability = dict()
traceability["nodes"] = dict()
traceability["edges"] = dict()


def add_trace(traceability_info: dict):
    """Adds an entry to the traceability dictionary.
    """

    # traceability info entries: (itemname, [parentitem], file, line, length)
    global traceability

    if "parent_item" in traceability_info.keys():
        if "->" in traceability_info["item"]:
            type = "edges"
            for edge in traceability["edges"]:
                if edge == traceability_info["parent_item"]:
                    item = edge

        else:
            type = "nodes"
            for node in traceability["nodes"]:
                if node == traceability_info["parent_item"]:
                    item = node

        # check if parent item exists, otherwise can't add
        if not traceability_info["parent_item"] in traceability[type].keys():
            #print("Can't add traceability " + str(traceability_info))
            pass
        else:

            # Adding the highlighting of the lines to the link (GitHub's feature)
            url = convert_path_to_url(traceability_info["file"])
            if not "implicit" in url and not "heuristic" in url:
                url = url + "#L" + str(traceability_info["line"])

            item = traceability_info["item"]
            parent_item = traceability_info["parent_item"]

            # add dict for sub items if not present yet
            if not "sub_items" in traceability[type][parent_item].keys():
                traceability[type][parent_item]["sub_items"] = dict()

            exists = False
            for sub_item in traceability[type][parent_item]["sub_items"].keys():
                if sub_item == traceability_info["item"]:
                    exists = True
                    if (traceability[type][parent_item]["sub_items"][sub_item]["file"] != url or
                            traceability[type][parent_item]["sub_items"][sub_item]["line"] != traceability_info["line"] or
                            traceability[type][parent_item]["sub_items"][sub_item]["span"] != str(traceability_info["span"])):

                        traceability[type][parent_item]["sub_items"][item] = dict()
                        traceability[type][parent_item]["sub_items"][item]["file"] = url
                        traceability[type][parent_item]["sub_items"][item]["line"] = traceability_info["line"]
                        traceability[type][parent_item]["sub_items"][item]["span"] = str(traceability_info["span"])

            # sub item does not exist yet
            if not exists:
                traceability[type][parent_item]["sub_items"][item] = dict()
                traceability[type][parent_item]["sub_items"][item]["file"] = url
                traceability[type][parent_item]["sub_items"][item]["line"] = traceability_info["line"]
                traceability[type][parent_item]["sub_items"][item]["span"] = str(traceability_info["span"])


    else:
        # Adding the highlighting of the lines to the link (GitHub's feature)
        url = convert_path_to_url(traceability_info["file"])
        if not "implicit" in url and not "heuristic" in url:
            url = url + "#L" + str(traceability_info["line"])

        # check, whether item is already in dict
        exists = False

        if "->" in traceability_info["item"]:
            type = "edges"
        else:
            type = "nodes"

        for item in traceability[type].keys():
            if item == traceability_info["item"]:
                exists = True
                if (not traceability[type][item]["file"] == url
                    or not traceability[type][item]["line"] == traceability_info["line"]
                    or not traceability[type][item]["span"] == str(traceability_info["span"])):

                    item = traceability_info["item"]
                    traceability[type][item] = dict()
                    traceability[type][item]["file"] = url
                    traceability[type][item]["line"] = traceability_info["line"]
                    traceability[type][item]["span"] = str(traceability_info["span"])
                break

        # item doesn't exist yet -> add it
        if not exists:
            item = traceability_info["item"]
            traceability[type][item] = dict()
            traceability[type][item]["file"] = url
            traceability[type][item]["line"] = traceability_info["line"]
            traceability[type][item]["span"] = str(traceability_info["span"])

    return


def revert_flow(old_sender: str, old_receiver: str):
    """Changes direction of flow
    """

    global traceability

    to_delete = False

    for item in traceability["edges"].copy():
        if item == (old_sender + " -> " + old_receiver):
            #traceability["edges"][old_receiver + " -> " + old_sender] = dict()
            traceability["edges"][old_receiver + " -> " + old_sender] = traceability["edges"][item]
            to_delete = item

    if to_delete:
        del traceability["edges"][to_delete]


def convert_path_to_url(path: str) -> str:
    """ Resolves the passed path to the corresponding GitHub download url.
    """

    if "implicit" in path or "heuristic" in path:
        return path

    repo_path = tmp.tmp_config["Repository"]["path"]
    if "analysed_repositories" in path:
        path = ("/").join(path.split("/")[3:])
    url = "https://github.com/" + str(repo_path) + "/blob/master/" + str(path)

    return url


def output_traceability():
    """Cleans the traceability dict and writes it to an output file.
    """

    quotate_ids()
    write_to_file()

    return traceability


def quotate_ids():
    """Puts double quotes around all ids from sub_items to make it readable.
    """

    global traceability

    new_traceability = dict()

    for trace in traceability:
        if "sub_items" in traceability[trace]:
            new_subs = dict()
            for sub_trace in traceability[trace]["sub_items"]:
                new_subs[str(sub_trace)] = traceability[trace]["sub_items"][sub_trace]
            traceability[trace]["sub_items"] = new_subs

        new_traceability[str(trace)] = traceability[trace]
    traceability = new_traceability



def write_to_file():
    """Writes tracebility info from dict to json file.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    repo_path = repo_path.replace("/", "_")
    filename = "./output/traceability/" + repo_path + "_traceability.json"
    with open(filename, "w") as file:
        file.write(json.dumps(traceability, indent=4))
    return
