#!/usr/bin/env python3
#
# Author: Simon Schneider, 2023
# Contact: simon.schneider@tuhh.de

from configparser import ConfigParser
from datetime import datetime
import argparse

import core.dfd_extraction as dfd_extraction
import output_generators.logger as logger
import tmp.tmp as tmp
from core.file_interaction import get_local_path, clone_repo


def api_invocation(path: str) -> dict:
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

    clone_repo(repo_path, local_path)

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

    elif args.github_path is not None:
        repo_path = args.github_path.strip()

        ini_config = ConfigParser()
        ini_config.read('config/config.ini')
        for section in ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]:     #copying what is needed from config to temp
            if not tmp.tmp_config.has_section(section):
                tmp.tmp_config.add_section(section)
            for entry in ini_config[section]:
                tmp.tmp_config.set(section, entry, ini_config[section][entry])
    local_path = get_local_path(repo_path)
    clone_repo(repo_path, local_path)
    tmp.tmp_config.set("Repository", "path", repo_path) # overwrite with user-provided path
    tmp.tmp_config.set("Repository", "local_path", local_path)

    # calling the actual extraction
    dfd_extraction.perform_analysis()

    now = datetime.now()
    end_time = now.strftime("%H:%M:%S")

    print("\nStarted", start_time)
    print("Finished", end_time)


if __name__ == '__main__':
    main()
