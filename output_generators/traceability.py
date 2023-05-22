import ast

import tmp.tmp as tmp

traceability = dict()

def dev_print(message: str):
    """Prints messages only if development_mode is set to True.
    """

    development_mode = bool(ast.literal_eval(tmp.tmp_config["Analysis Settings"]["development_mode"]))

    if development_mode:
        print("[dev] " + str(message))
    return


def add_trace(traceability_info: dict):
    """Adds an entry to the traceability dictionary.
    """

    dev_print(traceability_info)

    # traceability info entries: (itemname, [parentitem], file, line, length)
    global traceability

    if "parent_item" in traceability_info.keys():
        for t in traceability.keys():
            if traceability[t]["item"] == traceability_info["parent_item"]:

                # Adding the highlighting of the lines to the link (GitHub's feature)
                url = convert_path_to_url(traceability_info["file"])
                highlighted_url = url + "#L" + str(traceability_info["line"])

                if not "sub_items" in traceability[t].keys():
                    traceability[t]["sub_items"] = dict()
                    traceability[t]["sub_items"][0] = dict()
                    traceability[t]["sub_items"][0]["item"] = traceability_info["item"]
                    traceability[t]["sub_items"][0]["file"] = highlighted_url
                    traceability[t]["sub_items"][0]["line"] = traceability_info["line"]
                    traceability[t]["sub_items"][0]["span"] = str(traceability_info["span"])
                else:
                    exists = False
                    add = False
                    for sub_item in traceability[t]["sub_items"].keys():
                        if traceability[t]["sub_items"][sub_item]["item"] == traceability_info["item"]:
                            exists = True

                            if (not traceability[t]["sub_items"][sub_item]["file"] == highlighted_url
                                or not traceability[t]["sub_items"][sub_item]["line"] == traceability_info["line"]
                                or not traceability[t]["sub_items"][sub_item]["span"] == str(traceability_info["span"])):
                                add = True

                    if add:
                        try:
                            id = max(traceability[t]["sub_items"].keys()) + 1
                        except:
                            id = 0
                        traceability[t]["sub_items"][id] = dict()
                        traceability[t]["sub_items"][id]["item"] = traceability_info["item"]
                        traceability[t]["sub_items"][id]["file"] = highlighted_url
                        traceability[t]["sub_items"][id]["line"] = traceability_info["line"]
                        traceability[t]["sub_items"][id]["span"] = str(traceability_info["span"])



                    if not exists:
                        try:
                            id = max(traceability[t]["sub_items"].keys()) + 1
                        except:
                            id = 0
                        traceability[t]["sub_items"][id] = dict()
                        traceability[t]["sub_items"][id]["item"] = traceability_info["item"]
                        traceability[t]["sub_items"][id]["file"] = highlighted_url
                        traceability[t]["sub_items"][id]["line"] = traceability_info["line"]
                        traceability[t]["sub_items"][id]["span"] = str(traceability_info["span"])

    else:
        # Adding the highlighting of the lines to the link (GitHub's feature)
        url = convert_path_to_url(traceability_info["file"])
        highlighted_url = url + "#L" + str(traceability_info["line"])

        exists = False
        for trace in traceability.keys():
            if traceability[trace]["item"] == traceability_info["item"]:
                exists = True
                if (not traceability[trace]["file"] == highlighted_url
                    or not traceability[trace]["line"] == traceability_info["line"]
                    or not traceability[trace]["span"] == str(traceability_info["span"])):

                    try:
                        id = max(traceability.keys()) + 1
                    except:
                        id = 0
                    traceability[id] = dict()
                    traceability[id]["item"] = traceability_info["item"]
                    traceability[id]["file"] = highlighted_url
                    traceability[id]["line"] = traceability_info["line"]
                    traceability[id]["span"] = str(traceability_info["span"])
                break

        if not exists:
            try:
                id = max(traceability.keys()) + 1
            except:
                id = 0
            traceability[id] = dict()
            traceability[id]["item"] = traceability_info["item"]
            traceability[id]["file"] = highlighted_url
            traceability[id]["line"] = traceability_info["line"]
            traceability[id]["span"] = str(traceability_info["span"])

    return


def revert_flow(old_sender: str, old_receiver: str):
    """Changes direction of flow
    """

    global traceability

    for t in traceability.keys():
        if traceability[t]["item"] == (old_sender + " -> " + old_receiver):
            traceability[t]["item"] = old_receiver + " -> " + old_sender


def convert_path_to_url(path: str) -> str:
    """ Resolves the passed path to the corresponding GitHub download url.
    """

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
    """Writes tracebility info from dict to file.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    repo_path = repo_path.replace("/", "--")
    filename = "./output/traceability/" + repo_path + ".txt"
    with open(filename, "w") as file:
        for trace in traceability.keys():
            file.write(str(traceability[trace]) + "\n")
    return
