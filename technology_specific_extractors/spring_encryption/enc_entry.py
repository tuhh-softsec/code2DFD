import core.file_interaction as fi
import core.technology_switch as tech_sw


def detect_spring_encryption(microservices: dict, information_flows: dict, dfd) -> dict:
    """Detects use of Spring's crypto module encryption functions.
    """

    microservices = detect_passwordEncoder(microservices, dfd)
    microservices = detect_bytesEncryptor(microservices, dfd)
    microservices = detect_keyGenerator(microservices, dfd)

    return microservices, information_flows


def detect_passwordEncoder(microservices: dict, dfd) -> dict:
    """Detetcs encryption with BCryptPasswordEncoder.
    """

    passwordencoders = ["BCryptPasswordEncoder", "Pbkdf2PasswordEncoder", "ShaPasswordEncoder"]
    encoders = set()

    for passwordencoder in passwordencoders:
        results = fi.search_keywords(passwordencoder)
        for r in results.keys():
            for line in results[r]["content"]:
                if "new " + passwordencoder in line:
                    if "= new " + passwordencoder in line:
                        encoders.add(line.split("=")[0].strip().split(" ")[-1])

    for encoder in encoders:
        results = fi.search_keywords(encoder)
        for r in results.keys():
            microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
            for line in results[r]["content"]:
                if encoder + ".encode" in line:
                    for m in microservices.keys():
                        if microservices[m]["servicename"] == microservice:
                            if "stereotype_instances" in microservices[m]:
                                microservices[m]["stereotype_instances"].append("encryption")
                            else:
                                microservices[m]["stereotype_instances"] = ["encryption"]

    return microservices


def detect_bytesEncryptor(microservices: dict, dfd) -> dict:
    """Detects uses of Spring Security's BytesEncryptor.
    """

    types = ["stronger", "standard", "text", "delux", "queryableText", "noOpText"]
    for type in types:
        results = fi.search_keywords("Encryptors " + type)
        for r in results.keys():
            stereotypes, tagged_values = False, False
            microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
            for line in results[r]["content"]:
                if "Encryptors." + type in line:
                    stereotypes = ["encryption"]
                    try:
                        password = line.split("Encryptors." + type + "(")[1].split(",")[0].strip()
                    except:
                        password = False
                    if password:
                        tagged_values = [("Encrypted String", password)]
            for m in microservices.keys():
                if microservices[m]["servicename"] == microservice:
                    if "stereotype_instances" in microservices[m]:
                        microservices[m]["stereotype_instances"] += stereotypes
                    else:
                        microservices[m]["stereotype_instances"] = stereotypes
                    if tagged_values:
                        if "tagged_values" in microservices[m]:
                            microservices[m]["tagged_values"] += tagged_values
                        else:
                            microservices[m]["tagged_values"] = tagged_values
    return microservices


def detect_keyGenerator(microservices: dict, dfd) -> dict:
    """Detetcs Spring Security's KeyGenerators.
    """

    # Generate list of keygenerators
    keygenerators = list()

    commands = ["string", "shared", "secureRandom"]
    results = fi.search_keywords("Keygenerator")
    for r in results.keys():
        for command in commands:
            for line in results[r]["content"]:
                if "Keygenerator." + command in line:
                    # Direct use
                    if "Keygenerator." + command + "().generateKey" in line:
                        microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
                        for m in microservices.keys():
                            if microservices[m]["servicename"] == microservice:
                                try:
                                    microservices[m]["stereotypes"].append("keygenerator")
                                except:
                                    microservices[m]["stereotypes"] = ["keygenerator"]
                    # Creation here, use later
                    else:
                        keygenerators.add(extract_keygenerator(line))

    # Find uses of the keygenerators
    for keygenerator in keygenerators:
        results = fi.search_keywords(keygenerator + ".generateKey")
        for r in results.keys():
            microservice = tech_sw.detect_microservice(results[r]["path"], dfd)
            for m in microservices.keys():
                if microservices[m]["servicename"] == microservice:
                    try:
                        microservices[m]["stereotypes"].append("keygenerator")
                    except:
                        microservices[m]["stereotypes"] = ["keygenerator"]

    return microservices


def extract_keygenerator(line: str) -> str:
    """Extracts name of a keygenerator from line provided as input.
    """

    keygenerator = str()
    if "=" in line:
        keygenerator = line.split("=")[0].split(" ")[-1].strip()

    return keygenerator
