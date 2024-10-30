import os
from pathlib import Path

from core.config import code2dfd_config


def write_plaintext(dfd):
    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]
    external_components = dfd["external_components"]

    output_path = code2dfd_config["Analysis Settings"]["output_path"]
    parts = Path(output_path).parts
    filename = f"{parts[-2]}--{parts[-1]}_results.txt"
    output_path = os.path.join(output_path, filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as output_file:
        if microservices:
            output_file.write("Microservices:\n")
            for m in microservices.keys():
                microservices[m].pop("image", None)
                microservices[m].pop("pom_path", None)
                microservices[m].pop("properties", None)
                output_file.write("\n" + str(microservices[m]))

        if information_flows:
            output_file.write("\n\nInformation Flows:\n")
            for i in information_flows.keys():
                output_file.write("\n" + str(information_flows[i]))

        if external_components:
            output_file.write("\n\nExternal Components:\n")
            for e in external_components.keys():
                output_file.write("\n" + str(external_components[e]))
