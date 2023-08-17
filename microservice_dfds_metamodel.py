"""
This is an extension of the component metamodel in metamodels/component_metamodel in CodeableModels [1].
It provides many ``component_type`` and ``connector_type`` subclasses for modelling various concepts
found in microservices and other service-based systems for the creation of DFDs.

[1]: https://github.com/uzdun/CodeableModels
"""

from codeable_models import CClass, CBundle, add_links, CStereotype, CMetaclass, CEnum, CAttribute
from metamodels.component_metamodel import *


## Component types
database_component = CMetaclass("Database", superclasses = component)
service = CMetaclass("Service", superclasses = component)
external_component = CMetaclass("External Component", superclasses = component)


## Stereotypes
# For services
internal = CStereotype("Internal", extended = service, attributes = {"Port": int, "Endpoints": str})
infrastructural = CStereotype("Infrastructural", extended = service, attributes = {"Port": int, "Endpoints": str})
local_logging = CStereotype("Local Logging", extended = [service, external_component, database_component], attributes = {"Logging Technology": str})
gateway = CStereotype("Gateway", extended = [service, external_component, database_component], attributes = {"Gateway": str, "Port": int})
service_discovery = CStereotype("Service Discovery", extended = [service, external_component, database_component], attributes = {"Service Discovery": str, "Port": int})
message_broker = CStereotype("Message Broker", extended = [service, external_component, database_component], attributes = {"Message Broker": str, "Port": int})
configuration_server = CStereotype("Configuration Server", extended = [service, external_component, database_component], attributes = {"Configuration Server": str, "Port": int})
client = CStereotype("Client", extended = [service, external_component, database_component], attributes = {"Client": str})
in_memory_data_store = CStereotype("In-Memory Data Store", extended = [service, external_component, database_component], attributes = {"In-Memory Data Store": str})
load_balancer = CStereotype("Load Balancer", extended = [service, external_component, database_component], attributes = {"Load Balancer": str})
server_side_load_balancer = CStereotype("Server-side Load Balancer", extended = [service, external_component, database_component], attributes = {"Load Balancer": str})
authentication_server = CStereotype("Authentication Server", extended = [service, external_component, database_component], attributes = {"Authentication Server": str, "Port": int})
authorization_server = CStereotype("Authorization Server", extended = [service, external_component, database_component], attributes = {"Authorization Server": str, "Port": int})
web_application = CStereotype("Web Application", extended = [service, external_component, database_component], attributes = {"Web Application": str, "Port": int})
logging_server = CStereotype("Logging Server", extended = [service, external_component, database_component], attributes = {'Logging Server': str, "Port": int})
monitoring_server = CStereotype("Monitoring Server", extended = [service, external_component, database_component], attributes = {'Monitoring Server': str, "Port": int})
monitoring_dashboard = CStereotype("Monitoring Dashboard", extended = [service, external_component, database_component], attributes = {'Monitoring Dashboard': str, "Port": int})
web_server = CStereotype("Web Server", extended = [service, external_component, database_component], attributes = {"Web Server": str, "Exposed Port": int})
database = CStereotype("Database", extended = [database_component, service], attributes = {"Database": str, "Databases": list, "Port": int})
administration_server = CStereotype("Administration Server", extended = [service, external_component, database_component], attributes = {"Administration Server": str, "Port": int})
deployment_server = CStereotype("Deployment Server", extended = [service, external_component, database_component], attributes = {"Deployment Server": str, "Port": int})
circuit_breaker = CStereotype("Circuit Breaker", extended = [service, external_component, database_component], attributes = {"Circuit Breaker": str})
stream_aggregator = CStereotype("Stream Aggregator", extended = [service, external_component, database_component], attributes = {"Stream Aggregator": str, "Port": int})
resource_server = CStereotype("Resource Server", extended = [service, external_component, database_component])
pre_authorized_endpoints = CStereotype("Pre-authorized endpoints", extended = [service, external_component, database_component], attributes = {"Pre-authorized Endpoints": list})
in_memory_authentication = CStereotype("In-memory Authentication", extended = [service, external_component, database_component])
plaintext_credentials = CStereotype("Plaintext Credentials", extended = [service, external_component, database_component], attributes = {"Username": str, "Password": str})
tracing_server = CStereotype("Tracing Server", extended = [service, external_component, database_component], attributes = {"Tracing Server": str, "Port": int})
metrics_server = CStereotype("Metrics Server", extended = [service, external_component, database_component], attributes = {"Metrics Server": str, "Port": int})
visualization = CStereotype("Visualization", extended = [service, external_component, database_component], attributes = {"Visualization": str, "Port": int})
search_engine = CStereotype("Search Engine", extended = [service, external_component, database_component], attributes = {"Search Engine": str, "Port": int})
encryption = CStereotype("Encryption", extended = [service, external_component, database_component])
tokenstore = CStereotype("Tokenstore", extended = [service, external_component, database_component])
token_server = CStereotype("Token Server", extended = [service, external_component, database_component])
proxy = CStereotype("Proxy", extended = [service, external_component, database_component], attributes = {"Proxy": str})
authentication_scope_all_requests = CStereotype("Authentication Scope All Requests", extended = [service, external_component, database_component])
authorization_scope_all_requests = CStereotype("Authorization Scope All Requests", extended = [service, external_component, database_component])
basic_authentication = CStereotype("Basic Authentication", extended = [service, external_component, database_component])
in_memory_authentication = CStereotype("In Memory Authentication", extended = [service, external_component, database_component])
csrf_disabled = CStereotype("CSRF Disabled", extended = [service, external_component, database_component])



# For external components
user_stereotype = CStereotype("User", extended = external_component)
entrypoint = CStereotype("Entrypoint", extended = [service, external_component, database_component])
exitpoint = CStereotype("Exitpoint", extended = [service, external_component, database_component])
github_repository = CStereotype("GitHub Repository", extended = external_component, attributes = {"URL": str})
external_database = CStereotype("External Database", extended = external_component, attributes = {"Database": str, "Port": int})
mail_server = CStereotype("Mail Server", extended = external_component, attributes = {"Mail Server": str, "Host": str, "Port": int})
external_website = CStereotype("External Website", extended = external_component, attributes = {"URL": str})


# For connectors
jdbc = CStereotype("JDBC", extended = connectors_relation)
http_protocol = CEnum("HTTP Protocol", values = ["HTTP", "HTTPS"])
restful_http = CStereotype("RESTful HTTP", extended = connectors_relation, attributes = {"protocol": CAttribute(type = http_protocol)})
circuit_breaker_link = CStereotype("Circuit Breaker Guarded", extended = connectors_relation, attributes = {"Circuit Breaker": str})
load_balanced_link = CStereotype("Load Balanced", extended = connectors_relation, attributes = {"Load Balancer": str})
authenticated_request = CStereotype("Authenticated Request", extended = connectors_relation)
authentication_with_plaintext_credentials = CStereotype("Authentication With Plaintext Credentials", extended = connectors_relation, attributes = {"Username": str, "Password": str})
feign_connection = CStereotype("Feign Connection", extended = connectors_relation)
ssl_enabled = CStereotype("SSl Enabled", extended = connectors_relation)
ssl_disabled = CStereotype("SSl Disabled", extended = connectors_relation)
auth_provider = CStereotype("Auth Provider", extended = connectors_relation)
plaintext_credentials_link = CStereotype("Plaintext Credentials", extended = connectors_relation, attributes = {"Password": str, "Username": str})
messaging = CStereotype("Messaging", superclasses = connector_type)
message_producer = CStereotype("Message Producer", superclasses = messaging, attributes = {"out_channels": list})
message_consumer = CStereotype("Message Consumer", superclasses = messaging, attributes = {"in_channels": list})
message_producer_rabbitmq = CStereotype("Message Producer", superclasses = messaging, attributes = {"Producer Exchange": str, "Routing Key": str})
message_consumer_rabbitmq = CStereotype("Message Consumer", superclasses = messaging, attributes = {"Consumer Exchange": str, "Queue": str})
message_producer_kafka = CStereotype("Message Producer", superclasses = messaging, attributes = {"Producer Topic": str})
message_consumer_kafka = CStereotype("Message Consumer", superclasses = messaging, attributes = {"Consumer Topic": str})
