import core.file_interaction as fi
import core.technology_switch as tech_sw
import output_generators.traceability as traceability


def detect_hystrix_dashboard(dfd):
    """Detects hystrix monitoring dashboards .
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    results = fi.search_keywords("@EnableHystrixDashboard")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@EnableHystrixDashboard" in line:
                for m in microservices.keys():
                    if microservices[m]["name"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("monitoring_dashboard")
                        except:
                            microservices[m]["stereotype_instances"] = ["monitoring_dashboard"]
                        try:
                            microservices[m]["tagged_values"].append(("Monitoring Dashboard", "Hystrix"))
                        except:
                            microservices[m]["tagged_values"] = [("Monitoring Dashboard", "Hystrix")]

                        trace = dict()
                        trace["parent_item"] = microservices[m]["name"]
                        trace["item"] = "monitoring_dashboard"
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]
                        traceability.add_trace(trace)

    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows


def detect_hystrix_circuit_breakers(dfd):
    """Detects HystrixCommand.
    """

    microservices = dfd["microservices"]
    information_flows = dfd["information_flows"]

    results = fi.search_keywords("@EnableHystrix")     # content, name, path
    for r in results.keys():
        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
        for line in results[r]["content"]:
            if "@EnableHystrix" in line and not "@EnableHystrixDashboard" in line:
                for m in microservices.keys():
                    if microservices[m]["name"] == microservice:
                        try:
                            microservices[m]["stereotype_instances"].append("circuit_breaker")
                        except:
                            microservices[m]["stereotype_instances"] = ["circuit_breaker"]
                        try:
                            microservices[m]["tagged_values"].append(("Circuit Breaker", "Hystrix"))
                        except:
                            microservices[m]["tagged_values"] = [("Circuit Breaker", "Hystrix")]

                        trace = dict()
                        trace["parent_item"] = microservices[m]["name"]
                        trace["item"] = "circuit_breaker"
                        trace["file"] = results[r]["path"]
                        trace["line"] = results[r]["line_nr"]
                        trace["span"] = results[r]["span"]
                        traceability.add_trace(trace)

    dfd["microservices"] = microservices
    dfd["information_flows"] = information_flows
