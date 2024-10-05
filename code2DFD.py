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
from core.file_interaction import get_output_path, get_local_path, clone_repo

CONFIG_SECTIONS = ["Analysis Settings", "Repository", "Technology Profiles", "DFD"]
COMMUNICATIONS_TECH_LIST = '[("RabbitMQ", "rmq"), ("Kafka", "kfk"), ("RestTemplate", "rst"),\
                            ("FeignClient", "fgn"), ("Implicit Connections", "imp"),\
                            ("Database Connections", "dbc"), ("HTML", "html"),\
                            ("Docker-Compose", "dcm")]'
DEFAULT_CONFIG = ConfigParser()
for section in CONFIG_SECTIONS:
    DEFAULT_CONFIG.add_section(section)
DEFAULT_CONFIG.set("Analysis Settings", "development_mode", "False")
DEFAULT_CONFIG.set("Technology Profiles", "communication_techs_list", COMMUNICATIONS_TECH_LIST)


def api_invocation(path: str) -> dict:
    """Entry function for when tool is called via API call.
    """

    print("New call for " + path)
    response = dict()

    start_time = datetime.now()

    logger.write_log_message("*** New execution ***", "info")
    logger.write_log_message("Copying config file to tmp file", "debug")

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

    if args.config_path is not None:
        # Copy config to tmp file
        tmp.tmp_config.read(args.config_path)
        repo_path = tmp.tmp_config.get("Repository", "path")

    elif args.github_path is not None:
        # global ini_config
        for section in CONFIG_SECTIONS:  # Copying what is needed from default to temp
            tmp.tmp_config.add_section(section)
            for entry in DEFAULT_CONFIG[section]:
                tmp.tmp_config.set(section, entry, DEFAULT_CONFIG[section][entry])
        repo_path = args.github_path.strip()
        tmp.tmp_config.set("Repository", "path", repo_path) # overwrite with user-provided path

    local_path = get_local_path(repo_path)
    clone_repo(repo_path, local_path)
    tmp.tmp_config.set("Repository", "local_path", local_path)
    tmp.tmp_config.set("Analysis Settings", "output_path", get_output_path(repo_path))

    # calling the actual extraction
    dfd_extraction.perform_analysis()

    now = datetime.now()
    end_time = now.strftime("%H:%M:%S")

    print("\nStarted", start_time)
    print("Finished", end_time)


if __name__ == '__main__':
    main()
