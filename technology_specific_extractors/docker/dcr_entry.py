import os

import core.file_interaction as fi
import tmp.tmp as tmp


def detect_port(path: str) -> int:
    """Extracts port from Dockerfile.
    """

    port = False
    repo_path = tmp.tmp_config["Repository"]["path"]

    local_repo_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])

    dirs = list()
    dirs.append(os.scandir(local_repo_path + "/" + "/".join(path.split("/")[:-1])))

    while dirs:
        dir = dirs.pop()
        for entry in dir:
            if entry.is_file():
                if entry.name.casefold() == "dockerfile":
                    with open(entry.path, "r") as file:
                        lines = file.readlines()
                    for line in lines:
                        line = line.casefold()
                        if "expose" in line:
                            port = line.split("expose")[1].split("/")[0].strip()
            elif entry.is_dir():
                dirs.append(os.scandir(entry.path))

    return port


def extract_port(download_url: str):
    """Looks for exposed port in dockerfile.
    """

    try:
        file = fi.file_as_lines(download_url)
        for line in file:
            line = line.casefold()
            if "expose" in line:
                port = line.split("expose")[1].split("/")[0].strip()
                return port
    except:
        return False
