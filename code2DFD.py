#!/usr/bin/env python3
#
# Author: Simon Schneider, 2023
# Contact: simon.schneider@tuhh.de
import os
from configparser import ConfigParser
from datetime import datetime
import argparse

import core.dfd_extraction as dfd_extraction
from output_generators.logger import logger
import tmp.tmp as tmp
from core.file_interaction import clone_repo

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

    logger.info("*** New execution ***")
    logger.debug("Copying config file to tmp file")

    # Overwrite repo_path from config file with the one from the API call
    # TODO add analysis of specific commit with Flask API
    repo_path = str(path)
    tmp.tmp_config.set("Repository", "path", repo_path)

    local_path = os.path.join(os.getcwd(), "analysed_repositories", *repo_path.split("/")[1:])
    tmp.tmp_config.set("Repository", "local_path", local_path)

    clone_repo(repo_path, local_path) # TODO use Pydriller

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
    parser.add_argument("--config_path", type=str, help="Path to the config file to use")
    parser.add_argument("--repo_path", type=str, help="Path to the repository as 'repository/path'")
    parser.add_argument("--development_mode", action='store_true', help="Switch on development mode")
    parser.add_argument("--commit", type=str, help="Analyze repository at this commit")
    # TODO add cli for url
    # TODO add cli for local path

    args = parser.parse_args()

    logger.info("*** New execution ***")
    logger.debug("Copying config file to tmp file")

    if args.config_path:
        # Copy config to tmp file
        tmp.tmp_config.read(args.config_path)

    else:
        # global ini_config
        for section in CONFIG_SECTIONS:  # Copying what is needed from default to temp
            tmp.tmp_config.add_section(section)
            for entry in DEFAULT_CONFIG[section]:
                tmp.tmp_config.set(section, entry, DEFAULT_CONFIG[section][entry])

    if args.repo_path:
        repo_path = args.repo_path.strip()
        tmp.tmp_config.set("Repository", "path", repo_path) # overwrite with user-provided path
    elif not tmp.tmp_config.has_option("Repository", "path"):
        raise AttributeError("Parameter 'repo_path' must be provided either in config file or by --repo_path")

    if args.development_mode:
        tmp.tmp_config.set("Analysis Settings", "development_mode", "True")

    if args.commit is not None:
        commit = args.commit[:7]
        tmp.tmp_config.set("Analysis Settings", "commit", commit)
    elif tmp.tmp_config.has_option("Analysis Settings", "commit"):
        commit = tmp.tmp_config.get("Analysis Settings", "commit")[:7]
        tmp.tmp_config.set("Analysis Settings", "commit", commit)

    local_path = os.path.join(os.getcwd(), "analysed_repositories")
    tmp.tmp_config.set("Repository", "local_path", local_path)

    dfd_extraction.perform_analysis()


if __name__ == '__main__':
    main()
