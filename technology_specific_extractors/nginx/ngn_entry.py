import ruamel.yaml

import core.external_components as ext
import core.file_interaction as fi
import core.technology_switch as tech_sw
import tmp.tmp as tmp
import output_generators.traceability as traceability


# The following is taken from ruamel.yaml's authro as a workaround for getting line count for str objects
# https://stackoverflow.com/questions/45716281/parsing-yaml-get-line-numbers-even-in-ordered-maps/45717104#45717104
class Str(ruamel.yaml.scalarstring.ScalarString):
    __slots__ = ('lc')

    style = ""

    def __new__(cls, value):
        return ruamel.yaml.scalarstring.ScalarString.__new__(cls, value)

class MyPreservedScalarString(ruamel.yaml.scalarstring.PreservedScalarString):
    __slots__ = ('lc')

class MyDoubleQuotedScalarString(ruamel.yaml.scalarstring.DoubleQuotedScalarString):
    __slots__ = ('lc')

class MySingleQuotedScalarString(ruamel.yaml.scalarstring.SingleQuotedScalarString):
    __slots__ = ('lc')

class MyConstructor(ruamel.yaml.constructor.RoundTripConstructor):
    def construct_scalar(self, node):

        if not isinstance(node, ruamel.yaml.nodes.ScalarNode):
            raise ruamel.yaml.constructor.ConstructorError(
                None, None,
                "expected a scalar node, but found %s" % node.id,
                node.start_mark)

        if node.style == '|' and isinstance(node.value, ruamel.yaml.compat.text_type):
            ret_val = MyPreservedScalarString(node.value)
        elif bool(self._preserve_quotes) and isinstance(node.value, ruamel.yaml.compat.text_type):
            if node.style == "'":
                ret_val = MySingleQuotedScalarString(node.value)
            elif node.style == '"':
                ret_val = MyDoubleQuotedScalarString(node.value)
            else:
                ret_val = Str(node.value)
        else:
            ret_val = Str(node.value)
        ret_val.lc = ruamel.yaml.comments.LineCol()
        ret_val.lc.line = node.start_mark.line
        ret_val.lc.col = node.start_mark.column
        return ret_val
# end of external code


def detect_nginx(microservices: dict, information_flows: dict, external_components: dict, dfd) -> dict:
    """Detects nginx web applications.
    """

    web_app = False
    port = False
    correct_id = False
    gateway = False

    for m in microservices.keys():
        if "nginx:" in microservices[m]["image"]:
            web_app = microservices[m]["servicename"]
            correct_id = m
            try:
                microservices[m]["stereotype_instances"].append("web_application")
            except:
                microservices[m]["stereotype_instances"] = ["web_application"]
            try:
                microservices[m]["tagged_values"].append(("Web Application", "Nginx"))
            except:
                microservices[m]["tagged_values"] = [("Web Application", "Nginx")]

    if not web_app:
        results = fi.search_keywords("FROM nginx:")
        for r in results:
            web_service = tech_sw.detect_microservice(results[r]["path"], dfd)
            if web_service:
                for m in microservices.keys():
                    if microservices[m]["servicename"] == web_service:
                        web_app = web_service
                        correct_id = m
                        if "stereotype_instances" in microservices[m]:
                            microservices[m]["stereotype_instances"].append("web_application")
                        else:
                            microservices[m]["stereotype_instances"] = [("web_application")]
                        if "tagged_values" in microservices[m]:
                            microservices[m]["tagged_values"].append(("Web Application", "Nginx"))
                        else:
                            microservices[m]["tagged_values"] = [("Web Application", "Nginx")]

            else:
                try:
                    id = max(microservices.keys()) + 1
                except:
                    id = 0
                microservices[id] = dict()

                local_repo_path = tmp.tmp_config["Repository"]["local_path"]
                docker_path = ("/").join(results[r]["path"].split("/")[:-1]) + "/"
                docker_path = docker_path.replace(local_repo_path, "")

                service_name = "web-app"
                # go through dockercompose and see if a build or image fits this. if yes, use that name
                raw_files = fi.get_file_as_yaml("docker-compose.yml")
                if len(raw_files) == 0:
                    raw_files = fi.get_file_as_yaml("docker-compose.yaml")
                if len(raw_files) == 0:
                    raw_files = fi.get_file_as_yaml("docker-compose*")
                if len(raw_files) == 0:
                    raw_files = fi.get_file_as_yaml("docker-compose*")
                docker_compose_content = raw_files[0]["content"]

                yaml = ruamel.yaml.YAML()
                yaml.Constructor = MyConstructor

                file = yaml.load(docker_compose_content)
                if "services" in file.keys():
                    for s in file.get("services"):
                        image = False
                        try:
                            image = file.get("services", {}).get(s).get("image")
                        except:
                            pass
                        try:
                            image = file.get("services", {}).get(s).get("build")
                        except:
                            pass
                        if image:
                            if image == docker_path:
                                service_name = s

                microservices[id]["servicename"] = service_name
                microservices[id]["image"] = "nginx"
                microservices[id]["type"] = "service"
                microservices[id]["docker_path"] = docker_path
                microservices[id]["properties"] = set()
                microservices[id]["stereotype_instances"] = [("web_application")]
                microservices[id]["tagged_values"] = [("Web Application", "Nginx")]
                correct_id = id

                trace = dict()
                trace["item"] = service_name
                trace["file"] = results[r]["path"]
                trace["line"] = results[r]["line_nr"]
                trace["span"] = results[r]["span"]

                traceability.add_trace(trace)

            # Look for config file
            config_name = False
            for line in results[r]["content"]:
                if "COPY " in line and ".conf" in line:
                    config_name = line.strip().split(" ")[1]
            if config_name:
                config_path = ("/").join(results[r]["path"].split("/")[:-1]) + "/" + config_name
                config_results = fi.get_file_as_lines(config_name)

                for cr in config_results:
                    if config_results[cr]["path"] == config_path:
                        # found config file. Check settings
                        for line_nr in range(len(config_results[cr]["content"])):
                            line2 = config_results[cr]["content"][line_nr]

                            if "upstream" in line2:
                                counter = line_nr
                                while not "}" in config_results[cr]["content"][counter]:
                                    line3 = config_results[cr]["content"][counter]
                                    if "server " in line3:
                                        parts = line3.split(" ")[1:]
                                        for part in parts:
                                            if part != "":
                                                target = part.strip().strip(";").strip()

                                        if ":" in target:
                                            target_service = target.split(":")[0]
                                            for m in microservices.keys():
                                                if microservices[m]["servicename"] == target_service:
                                                    gateway = microservices[m]["servicename"]
                                            if not gateway:
                                                target_port = target.split(":")[1]
                                                for m in microservices.keys():
                                                    for prop in microservices[m]["tagged_values"]:
                                                        if prop[0] == "Port" and int(prop[1]) == int(target_port):
                                                            gateway = microservices[m]["servicename"]
                                        else:
                                            for m in microservices.keys():
                                                if microservices[m]["servicename"] == target:
                                                    gateway = microservices[m]["servicename"]
                                    counter += 1
                            elif "listen " in line2:
                                try:
                                    parts = line2.strip().split(" ")
                                    for part in parts:
                                        if part != "":
                                            try:
                                                port = int(part.strip(";").strip())
                                            except:
                                                pass
                                except Exception as e:
                                    pass

    if web_app:
        if port and correct_id:
            if "tagged_values" in microservices[correct_id]:
                microservices[correct_id]["tagged_values"].append(("Port", port))
            else:
                microservices[correct_id]["tagged_values"] = [("Port", port)]

        # connection to gateway
        if not gateway:
            for m in microservices.keys():
                if "stereotype_instances" in microservices[m] and "gateway" in microservices[m]["stereotype_instances"]:
                    gateway = microservices[m]["servicename"]

        if gateway:
            # adjust gateway annotations
            for m in microservices.keys():
                if microservices[m]["servicename"] == gateway:
                    if "stereotype_instances" in microservices[m]:
                        if not "gateway" in microservices[m]["stereotype_instances"]:
                            microservices[m]["stereotype_instances"].append("gateway")

                            # check for service-discovery connection that has to be reverted
                            discovery_server = False
                            for mi in microservices.keys():
                                if "stereotype_instances" in microservices[mi] and "service_discovery" in microservices[mi]["stereotype_instances"]:
                                    discovery_server = microservices[mi]["servicename"]
                            if discovery_server:
                                for i in information_flows:
                                    if information_flows[i]["sender"] == gateway and information_flows[i]["receiver"] == discovery_server:
                                        information_flows[i]["sender"] = discovery_server
                                        information_flows[i]["receiver"] = gateway
                    else:
                        microservices[m]["stereotype_instances"] = ["gateway"]

            # Set connection between web app and gateway
            try:
                id = max(information_flows.keys()) + 1
            except:
                id = 0
            information_flows[id] = dict()
            information_flows[id]["sender"] = web_app
            information_flows[id]["receiver"] = gateway
            information_flows[id]["stereotype_instances"] = ["restful_http"]

            # Check if user exists
            user_exists = False
            for e in external_components.keys():
                if external_components[e]["name"] == "user":
                    user_exists = True

            if user_exists:
                # Divert flows between gateway and user
                for i in information_flows.keys():
                    if information_flows[i]["sender"] == gateway and information_flows[i]["receiver"] == "user":
                        information_flows[i]["sender"] = web_app
                    elif information_flows[i]["sender"] == "user" and information_flows[i]["receiver"] == gateway:
                        information_flows[i]["receiver"] = web_app

                    trace = dict()
                    trace["item"] = web_app + " -> user"
                    trace["file"] = "implicit"
                    trace["line"] = "implicit"
                    trace["span"] = "implicit"
                    traceability.add_trace(trace)

                    trace["item"] = "user -> " + web_app
                    traceability.add_trace(trace)
            else:
                # Add user
                external_components = ext.add_user(external_components)

                # Add flows between web_app and user
                information_flows = ext.add_user_connections(information_flows, web_app)

    return microservices, information_flows, external_components
