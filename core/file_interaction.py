import ast
import os
import re
import subprocess
from configparser import ConfigParser

import requests

import output_generators.logger as logger
import core.technology_switch as tech_sw
import tmp.tmp as tmp


ini_config = ConfigParser()
ini_config.read('config/config.ini')

count = 0
total_length = 0
done = False

query_cache = dict()
exception_counter_keyword = int()

repo_cache = dict()
exception_counter_repo = 0


def repo_downloaded(repo_folder: str) -> bool:
    """Checks if repository has been downloaded from GitHub already.
    """

    if os.path.isdir(repo_folder):
        return True
    return False


def download_repo(repo_path: str):
    """Downloads repository from GitHub for local querying.
    """

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])
    clone_URL = "https://github.com/" + repo_path + ".git"
    command = "git clone " + clone_URL + " " + local_repo_path

    os.system(command)

    return True


def detection_comment(file_name, line):
    """Checks if provided line is a comment. Based on language of the file, so only works for the ones with specified comment-delimiters.
    """

    language = file_name.split(".")[-1]
    if language == "js" and line.replace(" ", "")[:2] == "//":
        return True
    elif language == "java" and line.replace(" ", "")[:2] == "//":
        return True
    elif language == "yml" and line.replace(" ", "")[:1] == "#":
        return True
    return False


def detection_import(line):
    """Checks if provided line is an import statement.
    """

    try:
        if line.split()[0] == "import":
            return True
        else:
            return False
    except:
        return False


def detection_config(file_name):
    """Checks if provided file is a config file.
    """

    if "config" in file_name.casefold():
        return True
    else:
        return False


def extract_import(line):
    """Extracts modules from import lines. E.g.: input "import matplotlib.figure;" -> output "figure".
    """

    return line.split(".")[-1][:-1]


def extract_variable(line, submodule):
    """Extracts a variable that is changed based on some module.
    """

    new_keyword = False
    if "=" in line:         # line is an assignment
        new_keyword = line.split("=")[0].strip().split()[-1]
    else:       # line is declaration
        new_keyword = line.split(";")[0].strip().split()[-1]
    return new_keyword


def search_keywords(keywords: str):
    """Searches keywords locally using grep.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    repo_folder = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    results = dict()

    if not repo_downloaded(repo_folder):
        download_repo(repo_path)

    if type(keywords) == str:
        keywords = [keywords]

    for keyword in keywords:
        if keyword[-1] == "(":
            keyword = "\"" + keyword + "\""
        out = subprocess.Popen(['grep', '-rn', keyword, repo_folder], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        stdout, stderr = out.communicate()
        seen = set()
        for line in stdout.decode().splitlines():
            try:
                if line.split(":")[0] not in seen:
                    seen.add(line.split(":")[0])
                    full_path = line.split(":")[0]

                    if not "test" in full_path and len(full_path) >= 3 and not full_path[-3:] == ".md":
                        try:
                            path = full_path.split(repo_folder)[1].strip("/")
                        except:
                            path = "/"
                        line_nr = line.split(":")[1]
                        name = path.split("/")[-1]
                        code_line = ":".join(line.split(":")[2:])
                        span = re.search(keyword, code_line).span()
                        with open(full_path) as file:
                            content = file.readlines()

                        try:
                            id = max(results.keys()) + 1
                        except:
                            id = 0
                        results[id] = dict()
                        results[id]["content"] = content
                        results[id]["name"] = name
                        results[id]["path"] = path
                        results[id]["line_nr"] = line_nr
                        results[id]["span"] = str(span)
            except Exception as e:
                pass
    return results


def enrich_output(results: list, microservices: dict):
    """Adds fields "Config", "Import", and "Comment" to the outputs.
    """

    for o in results:
        o["Config"] = detection_config(o["Filename"])
        o["Import"] = detection_import(o["Line"])
        o["Comment"] = detection_comment(o["Filename"], o["Line"])
        o["Service"] = "None"
        microservices = [microservices[x]["servicename"] for x in microservices.keys()]
        for m in microservices.keys:
            if m in o["Path"]:
                o["Service"] = m
    return results


def pagList2lines(pagList) -> dict:
    """Converts paginated list into files as lines.
    """

    results = dict()
    for p in pagList:
        containing_files_URLs = extract_downloadURL(p)
        for file in containing_files_URLs.keys():
            f = containing_files_URLs[file]
            try:
                id = max(results.keys()) + 1
            except:
                id = 0
            results[id] = dict()

            results[id]["content"] = file_as_lines(f["download_url"])
            results[id]["name"] = f["name"]
            results[id]["path"] = f["path"]
            results[id]["url"] = f["download_url"]

        return results


def extract_downloadURL(files) -> dict:
    """Returns URL to pull files from a repo that contain provided keyword.
    """

    containing_files_URLs = dict()
    for f in files:
        try:
            id = max(containing_files_URLs.keys()) + 1
        except:
            id = 0
        containing_files_URLs[id] = dict()

        containing_files_URLs[id]["path"] = f.path
        containing_files_URLs[id]["download_url"] = f.download_url
        containing_files_URLs[id]["name"] = f.name
    return containing_files_URLs


def get_struct(repo):
    """Returns structure of the repo (folders and files) and prints it.
    """

    struct = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            struct.append(str(file_content)[18:-2])
    return struct


def file_as_lines(raw_file):
    """Downloads and splits raw file into lines.
    """

    local_path_parts = raw_file.split("githubusercontent.com/")[1].split("/")[1:]
    local_path_parts.pop(1)
    local_path = "./analysed_repositories/" + ("/").join(local_path_parts)

    try:
        with open(local_path, "r") as file:
            file_as_lines = file.readlines()
    except Exception as e:
        file_as_lines = requests.get(raw_file, stream = True).text.split("\n")
    return file_as_lines


def detect_microservice(file_path, dfd):
    """Finds microservice that a file belongs to.
    """

    microservices_set = tech_sw.get_microservices(dfd)
    microservices = [microservices_set[x]["servicename"] for x in microservices_set.keys()]

    file_path_parts = file_path.split("/")
    count = 0
    part = 0
    found = False

    while part < len(file_path_parts) and not found:
        for m in microservices:
            if m == file_path_parts[part]:
                microservice = m
                count += 1
        if count > 0:
            found = True
        part += 1
    if count == 1:
        return microservice
    else:
        print("\tFound " + str(count) + " microservices for file " + str(file_path) +". \
        \n\tPlease choose microservice that the file belongs to: ")
        i = 1
        for m in microservices:
            print("\t[" + str(i) + "] " + str(m))
            i += 1
        return microservices[int(input("\n\t > ")) - 1]


def find_variable(parameter: str, file) -> str:
    """ Looks for passed ´parameter´ in passed ´file´ or other files.
    """

    if parameter == "":
        return parameter
    if parameter[0] == "\"" and parameter[-1] == "\"":      # already string as needed, return this
        return parameter.strip("\"")

    elif "." in parameter:               # means that it refers to some other file -> look for that file, then go through lines
        try:
            parameter_variable = parameter.split(".")[-1]
            parameter_class = parameter.split(".")[-2]
            files_containing_class = search_keywords("class " + str(parameter_class))
            correct_file = None
            variable = None
            for filec in files_containing_class.keys():
                fc = files_containing_class[filec]
                for linec in range(len(fc["content"])):
                    if "class" in fc["content"][linec] and parameter_class in fc["content"][linec]:
                        correct_file = fc["name"]
                        inside_class_definition = True
                        lines_class = len(fc["content"]) - linec
                        i = 0
                        while inside_class_definition and i < lines_class:
                            if "}" in fc["content"][i]:
                                inside_class_definition = False
                            i += 1
                            if parameter_variable in fc["content"][linec + i] and "=" in fc["content"][linec + i]:
                                variable = fc["content"][linec + i].split("=")[1].strip().strip(";").strip().strip("\"")
            logger.write_log_message(f"Found {variable} in file {correct_file}", "info")
        except:
            logger.write_log_message(f"Could not find a definition for {parameter}", "info")
            return None
    else:           # means that it's a variable in this file -> go through lines to find it
        if parameter[-2:-1] == "()":
            return parameter
        else:
            try:
                parameter_variable = parameter
                for line in range(len(file["content"])):
                    if parameter_variable in file["content"][line] and "=" in file["content"][line] and ("private" in file["content"][line] or "public" in file["content"][line] or "protected" in file["content"][line]):
                        variable = file["content"][line].split("=")[1].strip().strip(";").strip().strip("\"")
                name = file["name"]
                logger.write_log_message(f"Found {variable} in this file ({name})", "info")
            except:
                logger.write_log_message(f"Could not find a definition for {parameter}", "info")
                return None
    return variable


def find_instances(class_of_interest: str) -> set:
    """For the input class name, finds instantiations of it and returns set of names of these objects.
    Uses regular expression for it. In case of wrong findings, the regex needs to be adjusted.
    """

    instances = set()
    files = search_keywords(class_of_interest)

    regex = re.compile("^ *\t*(private|protected|public) (final )?" + class_of_interest + "(<.*>)? \w+ *;")        # last part means: 0 or 1 <> with something in it, then whitespace, then any legal variable character as often as wanted, then whitespace if wanted, then semicolon
    re.ASCII
    for file in files.keys():
        f = files[file]
        for line in range(len(f["content"])):
            match = re.search(regex, f["content"][line])
            if match:
                object = f["content"][line].split(class_of_interest)[1].split(">")[-1].strip().strip(";").strip()
                instances.add(object)

    return instances


def resolve_url(url: str, microservice: str, dfd) -> str:
    """Tries to resolve a url into one of the microserices.
    """

    microservices = tech_sw.get_microservices(dfd)
    target_service = False

    if "http" in url:
        if "localhost" in url:
            url_parts = url.split("/")
            for url_part in url_parts:
                port = False
                try:
                    port = url_part.split(":")[1]
                except:
                    pass
                if port:
                    for m in microservices.keys():
                        for prop in microservices[m]["tagged_values"]:
                            if prop[0] == "Port":
                                if port == prop[1]:
                                    target_service = microservices[m]["servicename"]
        else:
            for m in microservices.keys():
                url_parts = url.split("/")
                for url_part in url_parts:
                    if microservices[m]["servicename"] in url_part.split(":")[0]:
                        target_service = microservices[m]["servicename"]
    elif url[0] == "$":  # is environment variable
        if microservice:
            for m in microservices.keys():
                if microservices[m]["servicename"] == microservice:
                    try:
                        if "Spring Config" in microservices[m]["properties"]:
                            for mi in microservices.keys():
                                if ("Configuration Server", "Spring Cloud Config") in microservices[mi]["tagged_values"]:
                                    pass
                    except Exception as e:
                        pass

    return target_service


def check_dockerfile(build_path: str):
    """Checks if under the service's build-path there is a dockerfile. If yes, returns it.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]

    # find docker-compose path, since build-path is relative to that
    raw_files = get_file_as_lines("docker-compose.yml")
    if len(raw_files) == 0:
        raw_files = get_file_as_lines("docker-compose.yaml")
    if len(raw_files) == 0:
        return
    docker_compose_path = raw_files[0]["path"]
    if docker_compose_path != "docker_compose.yaml" and docker_compose_path != "docker_compose.yml":
        docker_compose_path = ("/").join(docker_compose_path.split("/")[:-1])
        path = docker_compose_path + build_path.replace(repo_path, "").strip("-")
    else:
        path = build_path.replace(repo_path, "").strip("./-")

    lines = list()

    try:
        repo_path = tmp.tmp_config["Repository"]["path"]
        local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])
        dirs = list()
        dirs.append(os.scandir(local_repo_path + "/" + path))

        while dirs:
            dir = dirs.pop()
            for entry in dir:
                if entry.is_file():
                    if entry.name.casefold() == "dockerfile":
                        with open(entry.path, "r") as file:
                            lines = file.readlines()
                elif entry.is_dir():
                    dirs.append(os.scandir(entry.path))

    except:
        pass


    return lines


def file_exists(file_name: str, repo_path: str) -> bool:
    """Checks if a file exists in the repository.
    """

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    dirs = list()
    dirs.append(os.scandir(local_repo_path))

    while dirs:
        dir = dirs.pop()
        for entry in dir:
            if entry.is_file():
                if entry.name.casefold() == file_name:
                    return True
            elif entry.is_dir():
                dirs.append(os.scandir(entry.path))

    return False


def get_repo_contents_local(repo_path: str, path: str) -> set:
    """Creates a set of all files in the repository given as path.
    """

    repo = set()

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    if not repo_downloaded(local_repo_path):
        download_repo(repo_path)

    if path:
        local_repo_path = local_repo_path + "/" + path.strip("/")
    try:
        contents = os.scandir(local_repo_path)
    except Exception as e:
        return repo
    for content in contents:
        path = tmp.tmp_config["Repository"]["path"]
        download_url = "https://raw.githubusercontent.com/" + path + "/master/" + ("/").join(content.path.split("/")[3:])
        repo.add((content.name, download_url, content.path))

    contents.close()

    return repo


def get_file_as_yaml(filename: str) -> dict:
    """Looks for a file in the repository and downloads it if existing.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    files = dict()

    repo_folder = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])
    out = subprocess.Popen(['find', repo_folder, '-name', filename], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if stdout:
        for line in stdout.decode().splitlines():
            try:
                id = max(files.keys()) + 1
            except:
                id = 0
            files[id] = dict()

            with open(line, 'r') as file:
                files[id]["content"] = file.read()

            relative_path = line.split(repo_folder)[1].strip("/")
            files[id]["path"] = relative_path

    return files


def get_file_as_lines(filename: str) -> dict:
    """Looks for a file in the repository and downloads it if existing.
    """

    repo_path = tmp.tmp_config["Repository"]["path"]
    files = dict()

    repo_folder = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])
    out = subprocess.Popen(['find', repo_folder, '-name', filename], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if stdout:
        for line in stdout.decode().splitlines():
            try:
                id = max(files.keys()) + 1
            except:
                id = 0
            files[id] = dict()

            with open(line, 'r') as file:
                files[id]["content"] = file.readlines()

            files[id]["name"] = line.split("/")[-1]

            relative_path = line.split(repo_folder)[1].strip("/")
            files[id]["path"] = relative_path

    return files



#
