import tmp.tmp as tmp


plantuml_new = str()

def convert(codeable_models_path: str) -> str:
    """Creates (good looking) PlantUML file out of CodeableModels file.
    """

    global plantuml_new

    repo_path = tmp.tmp_config["Repository"]["path"]
    output_file_path = "./output/png/" + repo_path.replace("/", "--") + ".png"

    add_header()

    with open(codeable_models_path, 'r') as input_file:
        codeable_models = input_file.readlines()

    # Call appropriate conversion functions for each line
    for line in codeable_models:
        if "CClass(external_component" in line:
            add_external_entity(line)
        elif "CClass(service" in line:
            if "stereotype_instances" in line:
                if "database" in line.split("stereotype_instances")[1].split(",")[0]:
                    add_database(line)
                else:
                    add_service(line)
            else:
                add_service(line)
        elif "add_links(" in line:
            add_flow(line)

    add_footer()

    write_output(output_file_path)

    return plantuml_new, output_file_path


def add_header():
    """Adds the header of the file.
    """

    global plantuml_new

    plantuml_new += """
@startuml
skinparam monochrome true
skinparam ClassBackgroundColor White
skinparam defaultFontName Arial
skinparam defaultFontSize 11


digraph dfd2{
    node[shape=record]
"""

    return 0


def add_external_entity(line: str):
    """Takes line for external entity from old format, parses it, creates line in new format, and appends it to output string.
    """

    global plantuml_new

    # Parse old line
    stereotypes = set()
    tagged_values = set()
    name = line.split("=")[0].strip()
    if "stereotype_instances" in line:
        stereotypes = line.split("stereotype_instances =")[1].split("]")[0].split("[")[1].split(",")
    if "tagged_values" in line:
        tagged_values = line.split("tagged_values =")[1].split("}")[0].split("{")[1].split(",")

    # Create new line
    new_line = "        " + name + " [label = \"{External Entity: " + name + " | "
    for stereotype in stereotypes:
        new_line += "--" + stereotype.strip() + "--\\n"
    if tagged_values:
        for tagged_value in tagged_values:
            new_line += tagged_value.split(":")[0].strip() + ": " + tagged_value.split(":")[1].strip().strip("\"") + "\\n"
    new_line += "}\"];\n"

    # Append new line
    plantuml_new += new_line

    return


def add_database(line: str):
    """Takes line for database from old format, parses it, creates line in new format, and appends it to output string.
    """

    global plantuml_new

    # Parse old line
    stereotypes = set()
    tagged_values = set()
    name = line.split("=")[0].strip()
    if "stereotype_instances" in line:
        stereotypes = line.split("stereotype_instances =")[1].split("]")[0].split("[")[1].split(",")
    if "tagged_values" in line:
        tagged_values = line.split("tagged_values =")[1].split("}")[0].split("{")[1].split(",")

    # Create new line
    new_line = "        " + name + " [label = \"|{Service: " + name + " | "
    for stereotype in stereotypes:
        new_line += "--" + stereotype.strip() + "--\\n"
    for tagged_value in tagged_values:
        new_line += tagged_value.split(":")[0].strip() + ": " + tagged_value.split(":")[1].strip().strip("\"") + "\\n"
    new_line += "}\"]\n"

    # Append new line
    plantuml_new += new_line

    return


def add_service(line: str):
    """Takes line for services from old format, parses it, creates line in new format, and appends it to output string.
    """

    global plantuml_new

    # Parse old line
    stereotypes = set()
    tagged_values = set()
    name = line.split("=")[0].strip()
    if "stereotype_instances" in line:
        stereotypes = line.split("stereotype_instances =")[1].split("]")[0].split("[")[1].split(",")
    if "tagged_values" in line:
        tagged_values = line.split("tagged_values =")[1].split("}")[0].split("{")[1].split(",")

    # Create new line
    new_line = "        " + name + " [label = \"{Service: " + name + " | "
    for stereotype in stereotypes:
        new_line += "--" + stereotype.strip() + "--\\n"
    for tagged_value in tagged_values:
        if ":" in tagged_value:
            new_line += tagged_value.split(":")[0].strip() + ": " + tagged_value.split(":")[1].strip().strip("\"") + "\\n"
    new_line += "}\" shape = Mrecord];\n"

    # Append new line
    plantuml_new += new_line

    return


def add_flow(line: str):
    """Takes line for flows from old format, parses it, creates line in new format, and appends it to output string.
    """

    global plantuml_new

    stereotypes = set()
    tagged_values = set()

    # Parse old line
    sender = line.split("}")[0].split(":")[0].split("{")[1].strip()
    receiver = line.split("}")[0].split(":")[1].strip()

    if "stereotype_instances" in line:
        stereotypes = line.split("stereotype_instances =")[1].split("]")[0].split("[")[1].split(",")
    if "tagged_values" in line:
        tagged_values = line.split("tagged_values =")[1].split("}")[0].split("{")[1].split(",")

    # Create new line
    new_line = "        " + sender + " -> " + receiver + " [label = \" "
    for stereotype in stereotypes:
        new_line += "--" + stereotype.strip() + "--\\n"
    if tagged_values:
        for tagged_value in tagged_values:
            new_line += tagged_value.replace("\"", "") + "\\n"
    new_line += "\"]\n"

    # Append new line
    plantuml_new += new_line

    return


def add_footer():
    """Adds the footer of the file.
    """

    global plantuml_new
    plantuml_new += """
}
@enduml
"""

    return 0


def write_output(output_file_path):
    """Writes the new format to a file.
    """

    global plantuml_new

    with open(output_file_path, 'w+') as output_file:
        output_file.write(plantuml_new)

    return
