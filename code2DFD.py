#!/usr/bin/env python3
#
# Author: Simon Schneider, 2023
# Contact: simon.schneider@tuhh.de

import os
from configparser import ConfigParser
from datetime import datetime
import argparse

import core.dfd_extraction as dfd_extraction
import core.file_interaction as fi
import output_generators.logger as logger
import tmp.tmp as tmp


def api_invocation(path: str) -> str:
    """Entry function for when tool is called via API call.
    """

    print("New call for " + path)
    response = dict()

    start_time = datetime.now()

    logger.write_log_message("*** New execution ***", "info")
    logger.write_log_message("Copying config file to tmp file", "debug")

    # Copy config to tmp file
    ini_config = ConfigParser()
    ini_config.read('config/config.ini')
    for section in ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]:     #copying what is needed from config to temp
        if not tmp.tmp_config.has_section(section):
            tmp.tmp_config.add_section(section)
        for entry in ini_config[section]:
            tmp.tmp_config.set(section, entry, ini_config[section][entry])

    # Overwrite repo_path from config file with the one from the API call
    repo_path = str(path)
    tmp.tmp_config.set("Repository", "path", repo_path)

    local_path = get_local_path(repo_path)
    tmp.tmp_config.set("Repository", "local_path", local_path)

    if not fi.repo_downloaded(local_path):
        fi.download_repo(repo_path, local_path)

    # Call extraction
    codeable_models, traceability = dfd_extraction.perform_analysis()

    response["codeable_models_file"] = codeable_models
    response["traceability"] = traceability

    # Execution time
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    print(execution_time)
    response["execution_time"] = execution_time

    # Return result
    return response


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config_path", type=str, help="Path to the config file to use")
    source.add_argument("--github_path", type=str, help="Path to the repository on GitHub as 'repository/path'")
    now = datetime.now()
    start_time = now.strftime("%H:%M:%S")

    args = parser.parse_args()

    logger.write_log_message("*** New execution ***", "info")
    logger.write_log_message("Copying config file to tmp file", "debug")
    for section in ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]:
        if not tmp.tmp_config.has_section(section):
            tmp.tmp_config.add_section(section)

    if args.config_path is not None:
        # Copy config to tmp file
        ini_config = ConfigParser()
        ini_config.read(args.config_path)
        for section in ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]:     #copying what is needed from config to temp
            for entry in ini_config[section]:
                tmp.tmp_config.set(section, entry, ini_config[section][entry])
        repo_path = tmp.tmp_config.get("Repository", "path")
        local_path = get_local_path(repo_path)
        tmp.tmp_config.set("Repository", "local_path", local_path)
        clone_repo(repo_path, local_path)

    elif args.github_path is not None:
        repo_path = args.github_path.strip()
        local_path = get_local_path(repo_path)
        tmp.tmp_config.set("Repository", "local_path", local_path)
        clone_repo(repo_path, local_path)

        ini_config = ConfigParser()
        ini_config.read('config/config.ini')
        for section in ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]:     #copying what is needed from config to temp
            if not tmp.tmp_config.has_section(section):
                tmp.tmp_config.add_section(section)
            for entry in ini_config[section]:
                tmp.tmp_config.set(section, entry, ini_config[section][entry])
        tmp.tmp_config.set("Repository", "path", repo_path) # overwrite with user-provided path

    # calling the actual extraction
    dfd_extraction.perform_analysis()

    now = datetime.now()
    end_time = now.strftime("%H:%M:%S")

    print("\nStarted", start_time)
    print("Finished", end_time)


def get_local_path(repo_path):
    return os.path.join(os.getcwd(), "analysed_repositories", *repo_path.split("/")[1:])


def clone_repo(repo_path, local_path):
    # Create analysed_repositories folder in case it doesn't exist yet (issue #2)
    os.makedirs(os.path.join(os.getcwd(), "analysed_repositories"), exist_ok=True)
    if not fi.repo_downloaded(local_path):
        fi.download_repo(repo_path, local_path)


if __name__ == '__main__':
    main()
