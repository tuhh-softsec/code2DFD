import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from output_generators.logger import logger
from core.config import code2dfd_config


count = 0
total_length = 0
done = False

query_cache = dict()
exception_counter_keyword = int()

repo_cache = dict()
exception_counter_repo = 0


def detection_comment(file_name, line):
    """Checks if provided line is a comment. Based on language of the file, so only works for the ones with specified comment-delimiters.
    """

    language = os.path.splitext(file_name)[1]
    return (language == ".js" and line.replace(" ", "")[:2] == "//") or (
            language == ".java" and line.replace(" ", "")[:2] == "//") or (
            language == ".yml" and line.replace(" ", "")[:1] == "#")


def detection_import(line):
    """Checks if provided line is an import statement.
    """

    return line.startswith("import")


def detection_config(file_name):
    """Checks if provided file is a config file.
    """

    return "config" in file_name.casefold()


def extract_import(line):
    """Extracts modules from import lines. E.g.: input "import matplotlib.figure;" -> output "figure".
    """

    return line.split(".")[-1][:-1]


def extract_variable(line, submodule):
    """Extracts a variable that is changed based on some module.
    """

    return line.split("=")[0].strip().split()[-1] if "=" in line else line.split(";")[0].strip().split()[-1]


def search_keywords(keywords: str):
    """Searches keywords locally using grep.
    """

    repo_folder = code2dfd_config["Repository"]["local_path"]

    results = dict()

    if isinstance(keywords, str):
        keywords = [keywords]

    for keyword in keywords:
        if keyword[-1] == "(":
            keyword = "\"" + keyword + "\""
        out = subprocess.Popen(['grep', '-rn', keyword, repo_folder], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        seen = set()
        for line in stdout.decode().splitlines():
            if line.startswith("Binary file"):
                continue
            line_parts = line.split(":")
            if len(line_parts) < 3:
                continue
            full_path = line_parts[0]
            if full_path not in seen:
                seen.add(full_path)
                if not "test" in full_path and len(full_path) >= 3 and not os.path.splitext(full_path)[1] == ".md":
                    path = os.path.relpath(full_path, start=repo_folder)
                    name = os.path.basename(path)
                    line_nr = line_parts[1]
                    code_line = ":".join(line_parts[2:])
                    try:
                        match = re.search(keyword, code_line)
                    except Exception as e:
                        logger.info(f"Error in regex matching for regex keyword {keyword}: {e}")
                        match = None
                    if match is None:
                        continue
                    span = match.span()
                    try:
                        with open(full_path) as file:
                            content = file.readlines()
                    except:
                        content = False

                    if content:
                        id_ = max(results.keys(), default=-1) + 1
                        results[id_] = dict()
                        results[id_]["content"] = content
                        results[id_]["name"] = name
                        results[id_]["path"] = path
                        results[id_]["line_nr"] = line_nr
                        results[id_]["span"] = str(span)
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
                id_ = max(results.keys()) + 1
            except:
                id_ = 0
            results[id_] = dict()

            results[id_]["content"] = file_as_lines(f["path"])
            results[id_]["name"] = f["name"]
            results[id_]["path"] = f["path"]

        return results


def extract_downloadURL(files) -> dict:
    """Returns URL to pull files from a repo that contain provided keyword.
    """

    containing_files_URLs = dict()
    for f in files:
        try:
            id_ = max(containing_files_URLs.keys()) + 1
        except:
            id_ = 0
        containing_files_URLs[id_] = dict()

        containing_files_URLs[id_]["path"] = f.path
        containing_files_URLs[id_]["name"] = f.name
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


def file_as_lines(path):
    """Downloads and splits raw file into lines.
    """

    local_path = code2dfd_config.get("Repository", "local_path")
    local_path = os.path.join(local_path, path)

    with open(local_path, "r") as file:
        file_as_lines = file.readlines()
    return file_as_lines


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
            logger.info(f"Found {variable} in file {correct_file}")
        except:
            logger.info(f"Could not find a definition for {parameter}")
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
                logger.info(f"Found {variable} in this file ({name})")
            except:
                logger.info(f"Could not find a definition for {parameter}")
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
                obj = f["content"][line].split(class_of_interest)[1].split(">")[-1].strip().strip(";").strip()
                instances.add(obj)

    return instances


def resolve_url(url: str, microservice: str, dfd) -> str:
    """Tries to resolve a url into one of the microserices.
    """

    microservices = dfd["microservices"]
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
                                    target_service = microservices[m]["name"]
        else:
            for m in microservices.keys():
                url_parts = url.split("/")
                for url_part in url_parts:
                    if microservices[m]["name"] in url_part.split(":")[0]:
                        target_service = microservices[m]["name"]
    elif url[0] == "$":  # is environment variable
        if microservice:
            for m in microservices.keys():
                if microservices[m]["name"] == microservice:
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
    local_repo_path = code2dfd_config["Repository"]["local_path"]

    # find docker-compose path, since build-path is relative to that
    raw_files = get_file_as_lines("docker-compose.yml")
    if len(raw_files) == 0:
        raw_files = get_file_as_lines("docker-compose.yaml")
    if len(raw_files) == 0:
        return
    docker_compose_path = raw_files[0]["path"]  # TODO this assumes there is exactly 1 relevant docker-compose
    docker_compose_dir = os.path.dirname(docker_compose_path)

    build_path = PurePosixPath(build_path.strip("-'"))  # Build path is always posix, so resolve it accordingly
    build_path = os.path.normpath(build_path)

    docker_path = os.path.join(local_repo_path, os.path.join(docker_compose_dir, build_path))

    lines = list()

    dirs = list()

    if os.path.exists(docker_path):
        dirs.append(os.scandir(docker_path))
        while dirs:
            d = dirs.pop()
            for entry in d:
                if entry.is_file():
                    if entry.name.casefold() == "dockerfile":
                        with open(entry.path, "r") as file:
                            lines = file.readlines()
                elif entry.is_dir():
                    dirs.append(os.scandir(entry.path))

    return lines


def file_exists(file_name: str) -> bool:
    """Checks if a file exists in the repository.
    """

    local_repo_path = code2dfd_config["Repository"]["local_path"]

    dirs = list()
    dirs.append(os.scandir(local_repo_path))

    while dirs:
        d = dirs.pop()
        for entry in d:
            if entry.is_file():
                if entry.name.casefold() == file_name:
                    return True
            elif entry.is_dir():
                dirs.append(os.scandir(entry.path))

    return False


def get_repo_contents_local(path: str) -> set:
    """Creates a set of all files in the repository given as path.
    """

    repo = set()

    local_repo_path = code2dfd_config["Repository"]["local_path"]
    to_crawl = local_repo_path

    if path:
        to_crawl = os.path.join(local_repo_path, path)
    try:
        contents = os.scandir(to_crawl)
    except Exception as e:
        return repo
    for content in contents:
        repo.add((content.name, content.path))

    contents.close()

    return repo


def get_file_as_yaml(filename: str) -> dict:
    """Looks for a file in the repository and downloads it if existing.
    """

    files = dict()

    local_path = code2dfd_config["Repository"]["local_path"]
    out = subprocess.Popen(['find', local_path, '-name', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if stdout:
        for line in stdout.decode().splitlines():
            if os.path.isfile(line):
                id_ = max(files.keys(), default=-1) + 1
                files[id_] = dict()
                with open(line, 'r') as file:
                    files[id_]["content"] = file.read()

                files[id_]["path"] = os.path.relpath(line, start=local_path)

    return files


def get_file_as_lines(filename: str) -> dict:
    """Looks for a file in the repository and downloads it if existing.
    """

    files = dict()

    local_path = code2dfd_config["Repository"]["local_path"]
    out = subprocess.Popen(['find', local_path, '-name', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if stdout:
        for line in stdout.decode().splitlines():
            try:
                id_ = max(files.keys()) + 1
            except:
                id_ = 0
            files[id_] = dict()

            with open(line, 'r') as file:
                files[id_]["content"] = file.readlines()

            files[id_]["name"] = os.path.basename(line)

            files[id_]["path"] = os.path.relpath(line, start=local_path)

    return files
