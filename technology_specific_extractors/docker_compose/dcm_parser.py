import ast
import re

import ruamel.yaml

import output_generators.traceability as traceability
import technology_specific_extractors.environment_variables as env
import tmp.tmp as tmp


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


def extract_microservices(file_content, file_name) -> set:
    """ Extracts the list of microservices from the docker-compose file autonomously,
    i.e. without asking for user-input in case of errors.
    """

    yaml = ruamel.yaml.YAML()
    yaml.Constructor = MyConstructor

    file = yaml.load(file_content)

    image = False
    build = False
    if tmp.tmp_config.has_option("DFD", "microservices"):
        microservices_dict =  ast.literal_eval(tmp.tmp_config["DFD"]["microservices"])
    else:
        microservices_dict= dict()
    microservices_set = set()
    properties_dict = dict()

    if "services" in file.keys():
        for s in file.get("services"):
            port = False

            # Traceability
            lines = file_content.splitlines()
            line_number = file["services"][s].lc.line - 1
            length_tuple = re.search(s, lines[line_number]).span()
            span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
            trace = (file_name, line_number + 1, span)

            properties = set()
            exists = False

            correct_id = False
            if s == "networks":
                exists = True
            for id in microservices_dict.keys():
                if microservices_dict[id]["servicename"] == s:
                    exists = True
                    correct_id = id

            try:
                ports = file.get("services", {}).get(s).get("ports")
                port_nr = ports[0].split(":")[0].strip("\" -")

                if type(port_nr) == list:
                    port_nr = port_nr[0]
                line_number = file["services"][s]["ports"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)

            except:
                try:
                    ports = file.get("services", {}).get(s).get("ports")
                    port_nr = ports[0].split(":")[0].strip("\" -")
                    line_number = file["services"][s]["ports"].lc.line
                    length_tuple = re.search(port_nr, lines[line_number]).span()
                    span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                    port = (port_nr, file_name, line_number + 1, span)
                except:
                    pass
            try:
                new_image = file.get("services", {}).get(s).get("image")
                image = new_image
                for id in microservices_dict.keys():
                    pom_path = microservices_dict[id]["pom_path"]
                    if new_image.split("/")[-1] == pom_path.split("/")[-2]:
                        exists = True
                        if "pom_" in microservices_dict[id]["servicename"]:
                            microservices_dict[id]["servicename"] = s
            except:
                pass

            try:
                new_build = file.get("services", {}).get(s).get("build")
                build = new_build
                for id in microservices_dict.keys():
                    pom_path = microservices_dict[id]["pom_path"]
                    if new_build.split("/")[-1] == pom_path.split("/")[-2]:
                        exists = True
                        if "pom_" in microservices_dict[id]["servicename"]:
                            microservices_dict[id]["servicename"] = s
            except:
                pass

            # Properties
            # Password
            try:
                password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASSWORD")
                line_nr = file["services"][s]["environment"]["MONGODB_PASSWORD"].lc.line
                length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in password:
                    password = env.resolve_env_var(password)
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
            except Exception as e:
                pass



            try:
                password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASS")
                line_nr = file["services"][s]["environment"]["MONGODB_PASS"].lc.line
                length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in password:
                    password = env.resolve_env_var(password)
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
            except:
                pass
            # Username
            try:
                username = file.get("services", {}).get(s).get("environment").get("MONGODB_USERNAME")
                line_nr = file["services"][s]["environment"]["MONGODB_USERNAME"].lc.line
                length_tuple = re.search(username.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in username:
                    username = env.resolve_env_var(username)
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
            except:
                pass

            try:
                username = file.get("services", {}).get(s).get("environment").get("MONGODB_USER")
                line_nr = file["services"][s]["environment"]["MONGODB_USER"].lc.line
                length_tuple = re.search(username.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in username:
                    username = env.resolve_env_var(username)
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
            except:
                pass

            # Environment
            try:
                environment_entries = file.get("services", {}).get(s).get("environment")
                username, password = None, None
                for line_nr, entry in enumerate(environment_entries):
                    if "MONGODB_USERNAME" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MONGODB_USERNAME")
                        line_nr = file["services"][s]["environment"]["MONGODB_USERNAME"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MONGODB_USER" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MONGODB_USER")
                        line_nr = file["services"][s]["environment"]["MONGODB_USER"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MYSQL_USERNAME" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MYSQL_USERNAME")
                        line_nr = file["services"][s]["environment"]["MYSQL_USERNAME"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MYSQL_USER" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MYSQL_USER")
                        line_nr = file["services"][s]["environment"]["MYSQL_USER"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))

                    elif "MONGODB_PASSWORD" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASSWORD")
                        line_nr = file["services"][s]["environment"]["MONGODB_PASSWORD"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MONGODB_PASS" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASS")
                        line_nr = file["services"][s]["environment"]["MONGODB_PASS"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MYSQL_PASSWORD" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MYSQL_PASSWORD")
                        line_nr = file["services"][s]["environment"]["MYSQL_PASSWORD"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MYSQL_PASS" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MYSQL_PASS")
                        line_nr = file["services"][s]["environment"]["MYSQL_PASS"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
            except:
                pass

            # Port (Kafka)
            try:
                port_nr = file.get("services", {}).get(s).get("environment").get("KAFKA_ADVERTISED_PORT")
                line_number = file["services"][s]["environment"]["KAFKA_ADVERTISED_PORT"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)

            except:
                pass

            # Postgres
            try:
                password = file.get("services", {}).get(s).get("environment").get("POSTGRES_PASSWORD")
                line_nr = file["services"][s]["environment"]["POSTGRES_PASSWORD"].lc.line
                length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
            except:
                pass

            try:
                username = file.get("services", {}).get(s).get("environment").get("POSTGRES_USER")
                line_nr = file["services"][s]["environment"]["POSTGRES_USER"].lc.line
                length_tuple = re.search(username.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
            except:
                pass

            # Port via "Expose" (overrules "ports")
            try:
                ports = file.get("services", {}).get(s).get("expose")
                port_nr = ports[0].split(":")[0].strip("\" -")
                line_number = file["services"][s]["expose"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)
            except:
                try:
                    ports = file.get("services", {}).get(s).get("expose")
                    port_nr = ports[0].split(":")[0].strip("\" -")
                    line_number = file["services"][s]["expose"].lc.line
                    length_tuple = re.search(port_nr, lines[line_number]).span()
                    span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                    port = (port_nr, file_name, line_number + 1, span)
                except:
                    pass

            if not image:
                image = "image"
                if build:
                    image = build

            if not exists:
                # Have to filter here and only add those with a known image.
                # Otherwise, many dublicates will occur when developers call the services different in docker-compose than in Spring.application.name
                known_images = ["elasticsearch",
                                "kibana",
                                "logstash",
                                "grafana",
                                "kafka",
                                "rabbit",
                                "zookeeper",
                                "postgres",
                                "zipkin",
                                "prometheus",
                                "mongo",
                                "consul",
                                "mysql",
                                "scope",
                                "postgres",
                                "apache",
                                "nginx"
                                ]
                for ki in known_images:
                    if ki in image:
                        properties_dict[s] = properties
                        microservices_set.add((s, image, "type", port, trace))
                        break

            # add additional information
            if exists and correct_id:
                if "properties" in microservices_dict[correct_id]:
                    microservices_dict[correct_id]["properties"] |= properties
                else:
                    microservices_dict[correct_id]["properties"] = properties

    else:
        for s in file.keys():
            port = False

            # Traceability
            lines = file_content.splitlines()
            line_number = file[s].lc.line - 1
            length_tuple = re.search(s, lines[line_number]).span()
            span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
            trace = (file_name, line_number + 1, span)

            properties = set()
            exists = False

            correct_id = False
            if s == "networks":
                exists = True
            for id in microservices_dict.keys():
                if microservices_dict[id]["servicename"] == s:
                    exists = True
                    correct_id = id

            try:
                ports = file.get(s).get("ports")
                port_nr = ports[0].split(":")[0].strip("\" -")

                if type(port_nr) == list:
                    port_nr = port_nr[0]
                line_number = file[s]["ports"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)
            except:
                try:
                    ports = file.get(s).get("ports")
                    port_nr = ports[0].split(":")[0].strip("\" -")
                    line_number = file[s]["ports"].lc.line
                    length_tuple = re.search(port_nr, lines[line_number]).span()
                    span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                    port = (port_nr, file_name, line_number + 1, span)
                except:
                    pass
            try:
                new_image = file.get(s).get("image")
                image = new_image
                for id in microservices_dict.keys():
                    pom_path = microservices_dict[id]["pom_path"]
                    if new_image.split("/")[-1] == pom_path.split("/")[-2]:
                        exists = True
                        if "pom_" in microservices_dict[id]["servicename"]:
                            microservices_dict[id]["servicename"] = s
            except:
                pass

            try:
                new_build = file.get(s).get("build")
                build = new_build
                for id in microservices_dict.keys():
                    pom_path = microservices_dict[id]["pom_path"]
                    if new_build.split("/")[-1] == pom_path.split("/")[-2]:
                        exists = True
                        if "pom_" in microservices_dict[id]["servicename"]:
                            microservices_dict[id]["servicename"] = s
            except:
                pass

            # Properties
            # Password
            try:
                password = file.get(s).get("environment").get("MONGODB_PASSWORD")
                line_number = file[s]["environment"]["MONGODB_PASSWORD"].lc.line - 1
                length_tuple = re.search(password.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in password:
                    password = env.resolve_env_var(password)
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_number + 1, span)))
            except:
                pass

            try:
                password = file.get(s).get("environment").get("MONGODB_PASS")
                line_number = file[s]["environment"]["MONGODB_PASS"].lc.line - 1
                length_tuple = re.search(password.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in password:
                    password = env.resolve_env_var(password)
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_number + 1, span)))
            except:
                pass
            # Username
            try:
                username = file.get(s).get("environment").get("MONGODB_USERNAME")
                line_number = file[s]["environment"]["MONGODB_USERNAME"].lc.line - 1
                length_tuple = re.search(username.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in username:
                    username = env.resolve_env_var(username)
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_number + 1, span)))
            except:
                pass

            try:
                username = file.get(s).get("environment").get("MONGODB_USER")
                line_number = file[s]["environment"]["MONGODB_USER"].lc.line - 1
                length_tuple = re.search(username.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if "$" in username:
                    username = env.resolve_env_var(username)
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_number + 1, span)))
            except:
                pass

            # Environment
            try:
                environment_entries = file.get(s).get("environment")
                username, password = None, None
                for line_nr, entry in enumerate(environment_entries):
                    if "MONGODB_USERNAME" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MONGODB_USERNAME")
                        line_nr = file["services"][s]["environment"]["MONGODB_USERNAME"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MONGODB_USER" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MONGODB_USER")
                        line_nr = file["services"][s]["environment"]["MONGODB_USER"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MYSQL_USERNAME" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MYSQL_USERNAME")
                        line_nr = file["services"][s]["environment"]["MYSQL_USERNAME"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))
                    elif "MYSQL_USER" in entry:
                        username = file.get("services", {}).get(s).get("environment").get("MYSQL_USER")
                        line_nr = file["services"][s]["environment"]["MYSQL_USER"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if username != None:
                            properties.add(("datasource_username", username, (file_name, line_nr + 1, span)))

                    elif "MONGODB_PASSWORD" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASSWORD")
                        line_nr = file["services"][s]["environment"]["MONGODB_PASSWORD"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MONGODB_PASS" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MONGODB_PASS")
                        line_nr = file["services"][s]["environment"]["MONGODB_PASS"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MYSQL_PASSWORD" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MYSQL_PASSWORD")
                        line_nr = file["services"][s]["environment"]["MYSQL_PASSWORD"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
                    elif "MYSQL_PASS" in entry:
                        password = file.get("services", {}).get(s).get("environment").get("MYSQL_PASS")
                        line_nr = file["services"][s]["environment"]["MYSQL_PASS"].lc.line
                        length_tuple = re.search(password.replace("$", "\$"), lines[line_nr].replace("$", "\$")).span()
                        span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                        if password != None:
                            properties.add(("datasource_password", password, (file_name, line_nr + 1, span)))
            except:
                pass

            # Port (Kafka)
            try:
                port_nr = file.get(s).get("environment").get("KAFKA_ADVERTISED_PORT")
                line_number = file[s]["environment"]["KAFKA_ADVERTISED_PORT"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)

            except:
                pass

            # Postgres
            try:
                password = file.get(s).get("environment").get("POSTGRES_PASSWORD")
                line_number = file[s]["environment"]["POSTGRES_PASSWORD"].lc.line - 1
                length_tuple = re.search(password.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if password != None:
                    properties.add(("datasource_password", password, (file_name, line_number + 1, span)))
            except:
                pass

            try:
                username = file.get(s).get("environment").get("POSTGRES_USER")
                line_number = file[s]["environment"]["POSTGRES_USER"].lc.line - 1
                length_tuple = re.search(username.replace("$", "\$"), lines[line_number].replace("$", "\$")).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                if username != None:
                    properties.add(("datasource_username", username, (file_name, line_number + 1, span)))
            except:
                pass

            # Port via "Expose" (overrules "ports")
            try:
                ports = file.get(s).get("expose")
                port_nr = ports[0].split(":")[0].strip("\" -")
                line_number = file[s]["expose"].lc.line - 1
                length_tuple = re.search(port_nr, lines[line_number]).span()
                span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                port = (port_nr, file_name, line_number + 1, span)
            except:
                try:
                    ports = file.get(s).get("expose")
                    port_nr = ports[0].split(":")[0].strip("\" -")
                    line_number = file[s]["expose"].lc.line
                    length_tuple = re.search(port_nr, lines[line_number]).span()
                    span = "[" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + "]"
                    port = (port_nr, file_name, line_number + 1, span)
                except:
                    pass

            if not image:
                image = "image"
                if build:
                    image = build

            if not exists:
                # Have to filter here and only add those with a known image.
                # Otherwise, many dublicates will occur when developers call the services different in docker-compose than in Spring.application.name
                known_images = ["elasticsearch",
                                "kibana",
                                "logstash",
                                "grafana",
                                "kafka",
                                "rabbit",
                                "zookeeper",
                                "postgres",
                                "zipkin",
                                "prometheus",
                                "mongo",
                                "consul",
                                "mysql",
                                "scope",
                                "postgres",
                                "apache",
                                "nginx"
                                ]
                for ki in known_images:
                    if ki in image:
                        properties_dict[s] = properties
                        microservices_set.add((s, image, "type", port, trace))
                        break

            # add additional information
            if exists and correct_id:
                if "properties" in microservices_dict[correct_id]:
                    microservices_dict[correct_id]["properties"] |= properties
                else:
                    microservices_dict[correct_id]["properties"] = properties

    tmp.tmp_config.set("DFD", "microservices", str(microservices_dict))
    return microservices_set, properties_dict


def extract_information_flows(file_content, microservices, information_flows):
    """Adds information flows based on "links".
    """

    yaml = ruamel.yaml.YAML()
    yaml.Constructor = MyConstructor

    discovery_server, config_server = False, False
    for m in microservices.keys():
        if "stereotype_instances" in microservices[m] and "service_discovery" in microservices[m]["stereotype_instances"]:
            discovery_server = microservices[m]["servicename"]
        if "stereotype_instances" in microservices[m] and "configuration_server" in microservices[m]["stereotype_instances"]:
            config_server = microservices[m]["servicename"]

    file = yaml.load(file_content)

    if "services" in file:
        for s in file.get("services"):

            try:
                links = file.get("services", {}).get(s).get("links")
                for link in links:
                    found_service = False
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == link:
                            found_service = True
                    if found_service and not link in {discovery_server, config_server}:
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = s
                        information_flows[id]["receiver"] = link
                        information_flows[id]["stereotype_instances"] = ["restful_http"]

            except:
                pass
    else:
        for s in file.keys():
            try:
                links = file.get(s).get("links")
                for link in links:
                    found_service = False
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == link:
                            found_service = True
                    if found_service and not link in {discovery_server, config_server}:
                        try:
                            id = max(information_flows.keys()) + 1
                        except:
                            id = 0
                        information_flows[id] = dict()
                        information_flows[id]["sender"] = s
                        information_flows[id]["receiver"] = link
                        information_flows[id]["stereotype_instances"] = ["restful_http"]
            except:
                pass
    return information_flows
