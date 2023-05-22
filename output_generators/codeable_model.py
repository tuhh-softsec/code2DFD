import tmp.tmp as tmp

plantuml_path = "plantuml.jar"
output_directory = "output/codeable_models"

# the used metamodel is microservice_dfds_metamodel.py

def output_codeable_model(microservices, information_flows, external_components):
    """Entry function to creation of codeable models. Calls all necessary helper functions and outputs the codeable model"""

    model_name = tmp.tmp_config["Repository"]["path"].split("/")[-1]

    file_content = header()
    file_content += "\"" + str(model_name) + "\""

    # CodeableModels needs the name of one of the nodes for its final invocation, is written into this var
    last_node = str()

    # Microservices
    for m in microservices.keys():
        # Tagged Values
        tagged_values = dict()
        if "tagged_values" in microservices[m]:
            for t in microservices[m]["tagged_values"]:
                if t[0] == "Port":
                    tagged_values[t[0]] = int(t[1])
                else:
                    tagged_values[t[0]] = t[1]

        # Stereotypes
        stereotypes = set()
        if "stereotype_instances" in microservices[m]:
            for s in microservices[m]["stereotype_instances"]:
                stereotypes.add(s)

            if stereotypes:
                stereotypes = str(list(stereotypes))
                stereotypes = stereotypes.replace("'", "")

        name = str(microservices[m]["servicename"]).replace("-", "_")

        # Create entry
        if stereotypes and tagged_values:
            new_line = "\n" + name + " = CClass(service, \"" + str(microservices[m]["servicename"]) + "\", stereotype_instances = " + str(stereotypes) + ", tagged_values = " + str(tagged_values) + ")"
        elif stereotypes:
            new_line = "\n" + name + " = CClass(service, \"" + str(microservices[m]["servicename"]) + "\", stereotype_instances = " + str(stereotypes) + ")"
        else:
            new_line = "\n" + name + " = CClass(service, \"" + str(microservices[m]["servicename"]) + "\")"

        file_content += new_line
        last_node = name


    # External Components
    for e in external_components.keys():
        # Tagged Values
        tagged_values = dict()
        if "tagged_values" in external_components[e]:
            for t in external_components[e]["tagged_values"]:
                if t[0] == "Port":
                    tagged_values[t[0]] = int(t[1])
                else:
                    tagged_values[t[0]] = t[1]

        # Stereotypes
        stereotypes = set()
        if "stereotype_instances" in external_components[e]:
            for s in external_components[e]["stereotype_instances"]:
                stereotypes.add(s)
            if stereotypes:
                stereotypes = str(list(stereotypes))
                stereotypes = stereotypes.replace("'", "")

        name = str(external_components[e]["name"]).replace("-", "_")


        if stereotypes and tagged_values:
            new_line = "\n" + name + " = CClass(external_component, \"" + str(external_components[e]["name"]) + "\", stereotype_instances = " + str(stereotypes) + ", tagged_values = " + str(tagged_values) + ")"
        elif stereotypes:
            new_line = "\n" + name + " = CClass(external_component, \"" + str(external_components[e]["name"]) + "\", stereotype_instances = " + str(stereotypes) + ")"
        else:
            new_line = "\n" + name + " = CClass(external_component, \"" + str(external_components[e]["name"]) + "\)"
        file_content += new_line


    # Information Flows
    for i in information_flows.keys():
        # Tagged Values
        tagged_values = dict()
        if "tagged_values" in information_flows[i]:
            for t in information_flows[i]["tagged_values"]:
                if t[0] == "Port":
                    t[1] = int(t[1])
                tagged_values[t[0]] = t[1]

        # Stereotypes
        stereotypes = set()
        if "stereotype_instances" in information_flows[i]:
            if type(information_flows[i]["stereotype_instances"]) == set or type(information_flows[i]["stereotype_instances"]) == list:
                for s in information_flows[i]["stereotype_instances"]:
                    stereotypes.add(s)
            else:
                stereotypes.add(information_flows[i]["stereotype_instances"])
            if stereotypes:
                stereotypes = str(list(stereotypes))
                stereotypes = stereotypes.replace("'", "")

        sender = str(information_flows[i]["sender"]).replace("-", "_")
        receiver = str(information_flows[i]["receiver"]).replace("-", "_")

        if stereotypes and tagged_values:
            new_line = "\nadd_links({" + sender + ": " + receiver + "}, stereotype_instances = " + str(stereotypes) + ", tagged_values = " + str(tagged_values) + ")"
        elif stereotypes:
            new_line = "\nadd_links({" + sender + ": " + receiver + "}, stereotype_instances = " + str(stereotypes) + ")"
        else:
            new_line = "\nadd_links({" + sender + ": " + receiver + "})"
        file_content += new_line


    file_content += footer(last_node)

    output_path = str()
    output_path = create_file(model_name, file_content)
    return file_content, output_path


def create_file(model_name: str, content: str):
    """Writes content to file.
    """

    model_name = model_name.replace("-", "_")
    file_path = "./output/codeable_models/" + model_name + ".py"
    file = open(file_path, "w")
    file.write(content)
    file.close()

    return file_path


def header():
    return "from codeable_models import CClass, CBundle, add_links, CStereotype, CMetaclass, CEnum, CAttribute \n\
from metamodels.microservice_dfds_metamodel import * \n\
from plant_uml_renderer import PlantUMLGenerator \n\
plantuml_path = \"../../plantuml.jar\" \n\
output_directory = \".\" \n\
model_name = "


def footer(last_node):
    return "\nmodel = CBundle(model_name, elements = " + last_node + ".class_object.get_connected_elements())\n\
def run():\n\
    generator = PlantUMLGenerator()\n\
    generator.plant_uml_jar_path = plantuml_path\n\
    generator.directory = output_directory\n\
    generator.object_model_renderer.left_to_right = True\n\
    generator.generate_object_models(model_name, [model, {}])\n\
    print(f\"Generated models in {generator.directory!s}/\" + model_name)\n\
if __name__ == \"__main__\":\n\
    run()"
