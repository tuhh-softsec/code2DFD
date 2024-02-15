import re

import requests
import ruamel.yaml

import core.file_interaction as fi
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




def parse_properties_file(download_url: str) -> str:
    """Extracts servicename from a .properties file.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    file_name = download_url.split(repo_path)[1].strip("/")

    properties = set()
    microservice = [False, False]

    file = fi.file_as_lines(download_url)

    i = 0
    for line in file:
        # Servicename
        if "spring.application.name" in line:
            if not "$" in line:
                microservice[0] = line.split("=")[1].strip()

                # Traceability
                microservice[1] = create_trace(microservice[0], file_name, file, i)

        # Port
        elif "server.port" in line:
                port = int(line.split("=")[1])
                if port:
                    span = re.search("server.port", line).span()
                    trace = (file_name, i, span)
                    properties.add(("port", port, trace))

        # Datasource
        elif "spring.datasource.url" in line:
            data_url = line.split("=")[1]
            if data_url:
                span = re.search("spring.datasource.url", line).span()
                trace = (file_name, i, span)
                properties.add(("datasource_url", data_url, trace))
        elif "spring.datasource.password" in line:
            password = line.split("=")[1]
            if password:
                span = re.search("spring.datasource.password", line).span()
                trace = (file_name, i, span)
                properties.add(("datasource_password", password, trace))
        elif "spring.datasource.username" in line:
            username = line.split("=")[1]
            if username:
                span = re.search("spring.datasource.username", line).span()
                trace = (file_name, i, span)
                properties.add(("datasource_username", username, trace))

        # Config
        elif "spring.cloud.config.server.git.uri" in line:
            config_uri = line.split("=")[1]
            if config_uri:
                span = re.search("spring.cloud.config.server.git.uri", line).span()
                trace = (file_name, i, span)
                properties.add(("config_repo_uri", config_uri, trace))
        elif "spring.cloud.config.uri" in line:
            config_uri = line.split("=")[1]
            if config_uri:
                span = re.search("spring.cloud.config.uri", line).span()
                trace = (file_name, i, span)
                properties.add(("config_uri", config_uri, trace))
                properties.add(("config_connected", True, trace))

        # SSL
        elif "server.ssl" in line:
            # Default for enabled is true when ssl keyword is given

            span = re.search("server.ssl", line).span()
            trace = (file_name, i, span)
            properties.add(("ssl_enabled", True, trace))
            # Check if disabled
            if "server.ssl.enabled" in line:
                ssl_enabled = line.split("=")[1]
                if ssl_enabled != None:
                    span = re.search("server.ssl.enabled", line).span()
                    trace = (file_name, i, span)
                    properties.add(("ssl_enabled", ssl_enabled, trace))

        # Eureka
        elif "eureka.client.serviceUrl.defaultZone" in line:
            span = re.search("eureka.client.serviceUrl.defaultZone", line).span()
            trace = (file_name, i, span)
            properties.add(("eureka_connected", True, trace))

        # Kafka
        elif "spring.cloud.stream.kafka.binder.brokers" in line:
            kafka_server = line.split("=")[1].strip().strip("\"").strip()
            span = re.search("spring.cloud.stream.kafka.binder.brokers", line).span()
            trace = (file_name, i, span)
            properties.add(("kafka_stream_binder", kafka_server, trace))
        elif "spring.cloud.stream.bindings.output.destination" in line:
            span = re.search("spring.cloud.stream.bindings.output.destination", line).span()
            trace = (file_name, i, span)
            properties.add(("kafka_stream_topic_out", line.split("=")[1].strip(), trace))
        elif "spring.cloud.stream.bindings.input.destination" in line:
            span = re.search("spring.cloud.stream.bindings.input.destination", line).span()
            trace = (file_name, i, span)
            properties.add(("kafka_stream_topic_in", line.split("=")[1].strip(), trace))

        # Admin server
        elif "spring.boot.admin.url" in line:
            span = re.search("spring.boot.admin.url", line).span()
            trace = (file_name, i, span)
            properties.add(("admin_server_url", line.split("=")[1].split(",")[0], trace))


        i += 1
    return microservice, properties


def parse_yaml_file(download_url: str, file_path: str) -> str:
    """Extracts servicename from a .yml or .yaml file.
    """


    yaml = ruamel.yaml.YAML()
    yaml.Constructor = MyConstructor

    properties = set()
    microservice = [False, False]
    lines = False
    try:    # local
        with open(file_path, "r") as file:
            lines = list()
            for line in file.readlines():
                lines.append(line.strip("\n"))
    except Exception as e:  # online
        raw_file = requests.get(download_url)
        lines = raw_file.text.splitlines()
    if not lines:
        return microservice, properties

    content = False
    try:    # local
        with open(file_path, "r") as file:
                content = file.read()
    except Exception as e:  # online
        raw_file = requests.get(download_url)
        content = raw_file.text
    if not content:
        return microservice, properties

    try:
        documents = yaml.load_all(content)
        for document in documents:
            # Zuul routes
            if "zuul" in document and "routes" in document.get("zuul"):
                    for route in document.get("zuul").get("routes"):
                        if "serviceId" in document.get("zuul").get("routes", {}).get(route):
                            serviceId = document.get("zuul").get("routes", {}).get(route).get("serviceId")
                            if serviceId != None:
                                for line_nr in range(len(lines)):
                                    if str(serviceId) in lines[line_nr]:
                                        span = re.search(re.escape(str(serviceId)), lines[line_nr]).span()
                                        trace = (file_path, line_nr + 1, span)
                                properties.add(("zuul_route_serviceId", serviceId, trace))
                        elif "url" in document.get("zuul").get("routes", {}).get(route):
                            url = document.get("zuul").get("routes", {}).get(route).get("url")
                            if url != None:
                                for line_nr in range(len(lines)):
                                    if str(url) in lines[line_nr]:
                                        span = re.search(re.escape(str(url)), lines[line_nr]).span()
                                        trace = (file_path, line_nr + 1, span)
                                properties.add(("zuul_route_url", url, trace))

            # Port
            if "server" in document and "port" in document.get("server"):
                    port = document.get("server").get("port")
                    trace = None

                    for line_nr in range(len(lines)):
                        if str(port) in lines[line_nr]:
                            span = re.search(re.escape(str(port)), lines[line_nr]).span()
                            trace = (file_path, line_nr + 1, span)

                    if port != None:
                        properties.add(("port", port, trace))

            if "server.port" in document:
                port = document.get("server.port")
                trace = None

                for line_nr in range(len(lines)):
                    if str(port) in lines[line_nr]:
                        span = re.search(re.escape(str(port)), lines[line_nr]).span()
                        trace = (file_path, line_nr + 1, span)
                if port != None:
                    properties.add(("port", port, trace))

            # Load Balancer
            if "ribbon" in document:
                load_balancer = document.get("ribbon")
                if load_balancer != None:
                    for nr in range(len(lines)):
                        if "ribbon" in lines[nr]:
                            line_nr = nr
                    span = re.search(re.escape("ribbon"), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("load_balancer", "Ribbon", trace))

            # Ciruit breaker
            if "hystrix" in document:
                circuit_breaker = document.get("hystrix")
                if circuit_breaker != None:
                    for nr in range(len(lines)):
                        if "hystrix" in lines[nr]:
                            line_nr = nr
                    trace = ("file", "line", "span")
                    properties.add(("circuit_breaker", "Hystrix", trace))

            # Eureka
            if "eureka" in document and "client" in document.get("eureka") and "serviceUrl" in document.get("eureka").get("client") and "defaultZone" in document.get("eureka").get("client").get("serviceUrl"):
                eureka_server = document.get("eureka").get("client").get("serviceUrl").get("defaultZone").split(",")[0]
                if eureka_server != None:
                    line_nr = document["eureka"]["client"]["serviceUrl"]["defaultZone"].lc.line
                    span = re.search(re.escape(eureka_server), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("eureka_connected", True, trace))

            # External api rates service
            if "rates" in document and "url" in document.get("rates"):
                    rates_url = document.get("rates").get("url")
                    if rates_url != None:
                        line_nr = document["rates"]["url"].lc.line
                        span = re.search(re.escape(rates_url), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("rates_url", rates_url, trace))

            # OAuth
            if "security" in document and "oauth2" in document.get("security") and "client" in document.get("security").get("oauth2"):
                if "accessTokenUri" in document.get("security").get("oauth2").get("client"):
                            oauth_tokenuri = document.get("security").get("oauth2").get("client").get("accessTokenUri")
                            if oauth_tokenuri != None:
                                line_nr = document["security"]["oauth2"]["client"]["accessTokenUri"].lc.line
                                span = re.search(re.escape(oauth_tokenuri), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("oauth_tokenuri", oauth_tokenuri, trace))

                if "access-token-uri" in document.get("security").get("oauth2").get("client"):
                                oauth_tokenuri = document.get("security").get("oauth2").get("client").get("access-token-uri")
                                if oauth_tokenuri != None:
                                    line_nr = document["security"]["oauth2"]["client"]["access-token-uri"].lc.line
                                    span = re.search(re.escape(oauth_tokenuri), lines[line_nr]).span()
                                    span = (span[0] + 1, span[1] + 1)
                                    trace = (file_path, line_nr + 1, span)
                                    properties.add(("oauth_tokenuri", oauth_tokenuri, trace))

                if "clientSecret" in document.get("security").get("oauth2").get("client"):
                                client_secret = document.get("security").get("oauth2").get("client").get("clientSecret")
                                if client_secret != None:
                                    line_nr = document["security"]["oauth2"]["client"]["clientSecret"].lc.line
                                    span = re.search(re.escape(client_secret), lines[line_nr]).span()
                                    span = (span[0] + 1, span[1] + 1)
                                    trace = (file_path, line_nr + 1, span)
                                    properties.add(("oauth_client_secret", client_secret, trace))

                if "clientId" in document.get("security").get("oauth2").get("client"):
                                client_id = document.get("security").get("oauth2").get("client").get("clientId")
                                if client_id != None:
                                    line_nr = document["security"]["oauth2"]["client"]["clientId"].lc.line
                                    span = re.search(re.escape(client_id), lines[line_nr]).span()
                                    span = (span[0] + 1, span[1] + 1)
                                    trace = (file_path, line_nr + 1, span)
                                    properties.add(("oauth_client_id", client_id, trace))

            if "security.oauth2.client" in document:
                if "clientId" in document.get("security.oauth2.client"):
                    client_id = document.get("security.oauth2.client").get("clientId")
                    if client_id != None:
                        line_nr = document["security"]["oauth2"]["client"]["clientId"].lc.line
                        span = re.search(re.escape(client_id), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("oauth_client_id", client_id, trace))

                    if "clientSecret" in document.get("security.oauth2.client"):
                        client_secret = document.get("security.oauth2.client").get("clientSecret")
                        if client_secret != None:
                            line_nr = document["security"]["oauth2"]["client"]["clientSecret"].lc.line
                            span = re.search(re.escape(client_secret), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("oauth_client_secret", client_secret, trace))


            # Feign
            if "feign" in document and "hystrix" in document.get("feign") and "enabled" in document.get("feign").get("hystrix"):
                        feign_hystrix = document.get("feign").get("hystrix").get("enabled")
                        if str(feign_hystrix).casefold() == "true":
                            trace = (file_path, "no lc for boolean", "no lc for boolean")
                            properties.add(("feign_hystrix", True, trace))

            if "spring" in document:
                # spring.config
                # Config
                if "config" in document.get("spring") and "import" in document.get("spring").get("config"):
                    config_connected = document.get("spring").get("config").get("import")
                    if config_connected != None:
                        line_nr = document["spring"]["config"]["import"].lc.line
                        span = re.search(re.escape(config_connected), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("config_connected", True, trace))

                # spring.cloud
                # Config
                if "cloud" in document.get("spring"):
                    if "config" in document.get("spring").get("cloud"):
                        if "uri" in document.get("spring").get("cloud").get("config"):
                            config_uri = document.get("spring").get("cloud").get("config").get("uri")
                            if config_uri != None:
                                line_nr = document["spring"]["cloud"]["config"]["uri"].lc.line
                                span = re.search(re.escape(config_uri), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("config_uri", config_uri, trace))
                                properties.add(("config_connected", True, trace))

                        if "discovery" in document.get("spring").get("cloud").get("config"):
                            if "service-id" in document.get("spring").get("cloud").get("config").get("discovery"):
                                config_uri = document.get("spring").get("cloud").get("config").get("discovery").get("service-id")
                                if config_uri != None:
                                    line_nr = document["spring"]["cloud"]["config"]["discovery"]["service-id"].lc.line
                                    span = re.search(re.escape(config_uri), lines[line_nr]).span()
                                    span = (span[0] + 1, span[1] + 1)
                                    trace = (file_path, line_nr + 1, span)
                                    properties.add(("config_uri", config_uri, trace))
                                    properties.add(("config_connected", True, trace))

                        if "password" in document.get("spring").get("cloud").get("config"):
                            config_password = document.get("spring").get("cloud").get("config").get("password")
                            if config_password != None:
                                line_nr = document["spring"]["cloud"]["config"]["password"].lc.line
                                span = re.search(re.escape(config_password), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("config_password", config_password, trace))

                        if "username" in document.get("spring").get("cloud").get("config"):
                            config_username = document.get("spring").get("cloud").get("config").get("username")
                            if config_username != None:
                                line_nr = document["spring"]["cloud"]["config"]["username"].lc.line
                                span = re.search(re.escape(config_username), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("config_username", config_username, trace))

                        # Config file (for config servers)
                        if "server" in document.get("spring").get("cloud").get("config"):
                            if "native" in document.get("spring").get("cloud").get("config").get("server"):
                                if "search-locations" in document.get("spring").get("cloud").get("config").get("server").get("native"):
                                    config_path = document.get("spring").get("cloud").get("config").get("server").get("native").get("search-locations")
                                    if ":" in config_path:
                                        complete_config_path = ("/").join(file_path.split("/")[:-1]) + "/" + config_path.split(":")[1].strip("/")
                                        if complete_config_path != None:
                                            line_nr = document["spring"]["cloud"]["config"]["server"]["native"]["search-locations"].lc.line
                                            properties.add(("config_file_path_local", complete_config_path, ("file", "line", "span")))


                                if "searchLocations" in document.get("spring").get("cloud").get("config").get("server").get("native"):
                                    config_path = document.get("spring").get("cloud").get("config").get("server").get("native").get("searchLocations")
                                    if ":" in config_path:
                                        complete_config_path = ("/").join(file_path.split("/")[:-1]) + "/" + config_path.split(":")[1]
                                        if complete_config_path != None:
                                            line_nr = document["spring"]["cloud"]["config"]["server"]["native"]["searchLocations"].lc.line
                                            span = re.search(re.escape(config_path), lines[line_nr]).span()
                                            span = (span[0] + 1, span[1] + 1)
                                            trace = (file_path, line_nr + 1, span)
                                            properties.add(("config_file_path_local", complete_config_path, trace))

                            if "git" in document.get("spring").get("cloud").get("config").get("server"):
                                if "search-uri" in document.get("spring").get("cloud").get("config").get("server").get("git"):
                                    config_uri = document.get("spring").get("cloud").get("config").get("server").get("git").get("search-uri")
                                    if config_uri != None:
                                        line_nr = document["spring"]["cloud"]["config"]["server"]["git"]["search-uri"].lc.line
                                        span = re.search(re.escape(config_uri), lines[line_nr]).span()
                                        span = (span[0] + 1, span[1] + 1)
                                        trace = (file_path, line_nr + 1, span)
                                        properties.add(("config_repo_uri", config_uri, trace))

                                if "uri" in document.get("spring").get("cloud").get("config").get("server").get("git"):
                                    config_uri = document.get("spring").get("cloud").get("config").get("server").get("git").get("uri")
                                    if config_uri != None:
                                        line_nr = document["spring"]["cloud"]["config"]["server"]["git"]["uri"].lc.line
                                        span = re.search(re.escape(config_uri), lines[line_nr]).span()
                                        span = (span[0] + 1, span[1] + 1)
                                        trace = (file_path, line_nr + 1, span)
                                        properties.add(("config_repo_uri", config_uri, trace))

                                if "searchPaths" in document.get("spring").get("cloud").get("config").get("server").get("git"):
                                    config_path = document.get("spring").get("cloud").get("config").get("server").get("git").get("searchPaths")
                                    if config_path != None:
                                        line_nr = document["spring"]["cloud"]["config"]["server"]["git"]["searchPaths"].lc.line
                                        span = re.search(re.escape(config_path), lines[line_nr]).span()
                                        span = (span[0] + 1, span[1] + 1)
                                        trace = (file_path, line_nr + 1, span)
                                        properties.add(("config_file_path", config_path, trace))

                    # Spring Cloud Gateway
                    if "gateway" in document.get("spring").get("cloud") and "routes" in document.get("spring").get("cloud").get("gateway"):
                        for route in document.get("spring").get("cloud").get("gateway").get("routes"):
                            if route != None:
                                line_nr = document["spring"]["cloud"]["gateway"]["routes"].lc.line
                                #span = re.search(re.escape(route), lines[line_nr]).span()
                                #span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, "span")
                                properties.add(("spring_cloud_gateway_route", route["id"], trace))

                    # Consul connection
                    if "consul" in document.get("spring").get("cloud") and "host" in document.get("spring").get("cloud").get("consul"):
                        consul = document.get("spring").get("cloud").get("consul").get("host")
                        if consul != None:
                            line_nr = document["spring"]["cloud"]["consul"]["host"].lc.line
                            span = re.search(re.escape(consul), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("consul_server", consul, trace))

                # spring.config
                if "config" in document.get("spring"):
                    config_connected = document.get("spring").get("config")
                    if config_connected != None:
                        line_nr = document["spring"]["config"].lc.line
                        trace = (file_path, line_nr + 1, "span")
                        properties.add(("config_connected", True, trace))

                # spring.rabbitmq
                if "rabbitmq" in document.get("spring"):
                    if "username" in document.get("spring").get("rabbitmq"):
                        rabbit_username = document.get("spring").get("rabbitmq").get("username")
                        if rabbit_username != None:
                            line_nr = document["spring"]["rabbitmq"]["username"].lc.line
                            span = re.search(re.escape(rabbit_username), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("rabbit_username", rabbit_username, trace))
                    if "password" in document.get("spring").get("rabbitmq"):
                        rabbit_password = document.get("spring").get("rabbitmq").get("password")
                        if rabbit_password != None:
                            line_nr = document["spring"]["rabbitmq"]["password"].lc.line
                            span = re.search(re.escape(rabbit_password), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("rabbit_password", rabbit_password, trace))

                # spring.mail
                # Mail
                if "mail" in document.get("spring"):
                    if "host" in document.get("spring").get("mail"):
                        mail_host = document.get("spring").get("mail").get("host")
                        if mail_host != None:
                            line_nr = document["spring"]["mail"]["host"].lc.line
                            span = re.search(re.escape(mail_host), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("mail_host", mail_host, trace))

                    if "username" in document.get("spring").get("mail"):
                        mail_username = document.get("spring").get("mail").get("username")
                        if mail_username != None:
                            line_nr = document["spring"]["mail"]["username"].lc.line
                            span = re.search(re.escape(mail_username), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("mail_username", mail_username, trace))

                    if "password" in document.get("spring").get("mail"):
                        mail_password = document.get("spring").get("mail").get("password")
                        if mail_password != None:
                            line_nr = document["spring"]["mail"]["password"].lc.line
                            span = re.search(re.escape(mail_password), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("mail_password", mail_password, trace))

                # spring.data
                # Datasources
                if "data" in document.get("spring"):
                    if "mongodb" in document.get("spring").get("data"):
                        if "host" in document.get("spring").get("data").get("mongodb"):
                            data_host = document.get("spring").get("data").get("mongodb").get("host")
                            if data_host != None:
                                line_nr = document["spring"]["data"]["mongodb"]["host"].lc.line
                                span = re.search(re.escape(data_host), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("datasource_host", data_host, trace))

                        if "password" in document.get("spring").get("data").get("mongodb"):
                            password = document.get("spring").get("data").get("mongodb").get("password")
                            if password != None:
                                line_nr = document["spring"]["data"]["mongodb"]["password"].lc.line
                                span = re.search(re.escape(password), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("datasource_password", password, trace))

                        if "username" in document.get("spring").get("data").get("mongodb"):
                            username = document.get("spring").get("data").get("mongodb").get("username")
                            if username != None:
                                line_nr = document["spring"]["data"]["mongodb"]["username"].lc.line
                                span = re.search(re.escape(username), lines[line_nr]).span()
                                span = (span[0] + 1, span[1] + 1)
                                trace = (file_path, line_nr + 1, span)
                                properties.add(("datasource_username", username, trace))

                    if "mongodb.uri" in document.get("spring").get("data"):
                        datasource_uri = document.get("spring").get("data").get("mongodb.uri")
                        if datasource_uri != None:
                            line_nr = document["spring"]["data"]["mongodb.uri"].lc.line
                            span = re.search(re.escape(datasource_uri), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("datasource_uri", datasource_uri, trace))

                # spring.datasource
                # Datasource
                if "datasource" in document.get("spring"):
                    if "url" in document.get("spring").get("datasource"):
                        data_url = document.get("spring").get("datasource").get("url")
                        if data_url != None:
                            line_nr = document["spring"]["datasource"]["url"].lc.line
                            span = re.search(re.escape(data_url), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("datasource_url", data_url, trace))

                    if "password" in document.get("spring").get("datasource"):
                        password = document.get("spring").get("datasource").get("password")
                        if password != None:
                            line_nr = document["spring"]["datasource"]["password"].lc.line
                            span = re.search(re.escape(password), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("datasource_password", password, trace))

                    if "username" in document.get("spring").get("datasource"):
                        username = document.get("spring").get("datasource").get("username")
                        if username != None:
                            line_nr = document["spring"]["datasource"]["username"].lc.line
                            span = re.search(re.escape(username), lines[line_nr]).span()
                            span = (span[0] + 1, span[1] + 1)
                            trace = (file_path, line_nr + 1, span)
                            properties.add(("datasource_username", username, trace))

                # spring.zipkin
                # Zipkin
                if "zipkin" in document.get("spring") and "base-url" in document.get("spring").get("zipkin"):
                    zipkin_url = document.get("spring").get("zipkin").get("base-url")
                    if zipkin_url != None:
                        line_nr = document["spring"]["zipkin"]["base-url"].lc.line
                        span = re.search(re.escape(zipkin_url), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("zipkin_url", zipkin_url, trace))

                if "zipkin" in document.get("spring") and "baseUrl" in document.get("spring").get("zipkin"):
                    zipkin_url = document.get("spring").get("zipkin").get("baseUrl")
                    if zipkin_url != None:
                        line_nr = document["spring"]["zipkin"]["baseUrl"].lc.line
                        span = re.search(re.escape(zipkin_url), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("zipkin_url", zipkin_url, trace))

                # spring.application
                # Servicename
                if "application" in document.get("spring") and "name" in document.get("spring").get("application"):
                    service = document.get("spring").get("application").get("name")
                    if service:
                        microservice[0] = service

                        # traceability
                        line_number = document["spring"]["application"]["name"].lc.line
                        microservice[1] = create_trace(service, file_path, lines, line_number)

                # spring.application.name
                if "application.name" in document.get("spring"):
                    service = document.get("spring").get("application.name")
                    if service:
                        microservice[0] = service

                        # traceability
                        line_number = document["spring"]["application.name"].lc.line - 1
                        microservice[1] = create_trace(service, file_path, lines, line_number)

            if "spring.application.name" in document:
                service = document.get("spring.application.name")
                if service:
                    microservice[0] = service

                    # traceability
                    line_number = document["spring.application.name"].lc.line - 1
                    microservice[1] = create_trace(service, file_path, lines, line_number)

            # Neo4j database
            if "neo4j" in document:
                if "uri" in document.get("neo4j"):
                    neo4j_uri = document.get("neo4j").get("uri")
                    if neo4j_uri != None:
                        line_nr = document["neo4j"]["uri"].lc.line
                        span = re.search(re.escape(neo4j_uri), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("datasource_url", neo4j_uri, trace))
                        properties.add(("datasource_type", "Neo4j", trace))

                if "password" in document.get("neo4j"):
                    neo4j_password = document.get("neo4j").get("password")
                    if neo4j_password != None:
                        line_nr = document["neo4j"]["password"].lc.line
                        span = re.search(re.escape(neo4j_password), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("datasource_password", neo4j_password, trace))

                if "username" in document.get("neo4j"):
                    neo4j_username = document.get("neo4j").get("username")
                    if neo4j_username != None:
                        line_nr = document["neo4j"]["username"].lc.line
                        span = re.search(re.escape(neo4j_username), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("datasource_username", neo4j_username, trace))

            # SSL
            # Default for enabled is true, when any configurations are made
            if "server" in document and "ssl" in document.get("server"):
                ssl_enabled = document.get("server").get("ssl")
                if ssl_enabled != None:
                    line_nr = document["server"]["ssl"].lc.line
                    span = re.search(re.escape(ssl_enabled), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("ssl_enabled", True, trace))

            # Check if disabled
                if "enabled" in document.get("server").get("ssl"):
                    ssl_enabled = document.get("server").get("ssl").get("enabled")
                    if ssl_enabled != None:
                        line_nr = document["server"]["ssl"]["enabled"].lc.line
                        span = re.search(re.escape(ssl_enabled), lines[line_nr]).span()
                        span = (span[0] + 1, span[1] + 1)
                        trace = (file_path, line_nr + 1, span)
                        properties.add(("ssl_enabled", ssl_enabled, trace))

            # Logstash connection
            if "logstash.servers" in document:
                logstash_server = document.get("logstash.servers")
                if logstash_server != None:
                    line_nr = document["logstash.servers"].lc.line
                    span = re.search(re.escape(logstash_server), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("logstash_server", logstash_server, trace))

            if "logstash" in document and "servers" in document.get("logstash"):
                logstash_server = document.get("logstash").get("servers")
                if logstash_server != None:
                    line_nr = document["logstash"]["servers"].lc.line
                    span = re.search(re.escape(logstash_server), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("logstash_server", logstash_server, trace))

            if "output" in document and "logstash" in document.get("output") and "hosts" in document.get("output").get("logstash"):
                logstash_server = document.get("output").get("logstash").get("hosts")[0]
                if logstash_server != None:
                    line_nr = document["output"]["logstash"]["hosts"].lc.line
                    span = re.search(re.escape(logstash_server), lines[line_nr]).span()
                    span = (span[0] + 1, span[1] + 1)
                    trace = (file_path, line_nr + 1, span)
                    properties.add(("logstash_server", logstash_server, trace))
    except Exception as e:
        pass

    return microservice, properties


def create_trace(keyword: str, file_name: str, lines: list, line_number: int) -> tuple:
    """Finds line number and span of a keyword.
    """

    trace = None

    match = re.search(re.escape(keyword), lines[line_number])

    if match:
        length_tuple = match.span()
        span = "(" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + ")"
        trace = (file_name, line_number + 1, span)
    else:
        line_number += 1
        match = re.search(re.escape(keyword), lines[line_number])
        if match:
            length_tuple = match.span()
            span = "(" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + ")"
            trace = (file_name, line_number + 1, span)
        else:
            line_number += 1
            match = re.search(re.escape(keyword), lines[line_number])
            if match:
                length_tuple = match.span()
                span = "(" + str(length_tuple[0]) +  ":" + str(length_tuple[1]) + ")"
                trace = (file_name, line_number + 1, span)
            else:
                trace = (file_name, line_number, "(0:0)")

    return trace
