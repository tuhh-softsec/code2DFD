#!/usr/bin/env python3
#
# Author: Simon Schneider, 2023
# Contact: simon.schneider@tuhh.de
import os
from configparser import ConfigParser
from datetime import datetime
import argparse

from core.dfd_extraction import perform_analysis
from output_generators.logger import logger
import tmp.tmp as tmp

CONFIG_SECTIONS = ["Analysis Settings", "Repository", "Technology Profiles"]
COMMUNICATIONS_TECH_LIST = '[("RabbitMQ", "rmq"), ("Kafka", "kfk"), ("RestTemplate", "rst"),\
                            ("FeignClient", "fgn"), ("Implicit Connections", "imp"),\
                            ("Database Connections", "dbc"), ("HTML", "html"),\
                            ("Docker-Compose", "dcm")]'
DEFAULT_CONFIG = ConfigParser()
for section in CONFIG_SECTIONS:
    DEFAULT_CONFIG.add_section(section)
DEFAULT_CONFIG.set("Analysis Settings", "development_mode", "False")
DEFAULT_CONFIG.set("Technology Profiles", "communication_techs_list", COMMUNICATIONS_TECH_LIST)


def api_invocation(url: str, commit: str) -> dict:
    """Entry function for when tool is called via API call.
    """

    print("New call for " + url)

    start_time = datetime.now()

    logger.info("*** New execution ***")
    logger.debug("Initializing config to tmp file")
    for section in CONFIG_SECTIONS:  # Copying what is needed from default to temp
        tmp.tmp_config.add_section(section)
        for entry in DEFAULT_CONFIG[section]:
            tmp.tmp_config.set(section, entry, DEFAULT_CONFIG[section][entry])

    # Overwrite repo_path from config file with the one from the API call
    tmp.tmp_config.set("Repository", "url", url)
    tmp.tmp_config.set("Repository", "local_path",
                       os.path.join(os.getcwd(), "analysed_repositories"))
    if commit is not None:
        tmp.tmp_config.set("Repository", "commit", commit)

    # Call extraction
    codeable_models, traceability = perform_analysis()

    response = dict()
    response["codeable_models_file"] = codeable_models
    response["traceability_file"] = traceability

    # Execution time
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    print(execution_time)
    response["execution_time"] = execution_time

    # Return result
    return response


def cli_invocation():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, help="Path to the config file to use (can be replaced with following CLI arguments")
    repository = parser.add_argument_group("Repository", "Repository information")
    repository.add_argument("--repo_url", type=str, help="URL to clone the repository from (might be local path)")
    repository.add_argument("--repo_local_path", type=str, help="Location to clone repository to (default: 'analysed_repositories' in CWD)")
    repository.add_argument("--github_handle", type=str, help="Handle of a GitHub repository containing the application to be analyzed")
    repository.add_argument("--commit", type=str, help="Analyze repository at this commit")
    settings = parser.add_argument_group("Analysis Settings", "Parameters for additional analysis settings")
    settings.add_argument("--development_mode", action='store_true', help="Switch on development mode")

    args = parser.parse_args()

    logger.info("*** New execution ***")

    if args.config_path:
        # Copy config to tmp file
        logger.debug("Copying config file to tmp file")
        tmp.tmp_config.read(args.config_path)
    else:
        # global ini_config
        logger.debug("Initializing tmp file with default config")
        for section in CONFIG_SECTIONS:  # Copying what is needed from default to temp
            tmp.tmp_config.add_section(section)
            for entry in DEFAULT_CONFIG[section]:
                tmp.tmp_config.set(section, entry, DEFAULT_CONFIG[section][entry])

    if args.repo_url:
        tmp.tmp_config.set("Repository", "url", args.repo_url)
    elif args.github_handle:
        tmp.tmp_config.set("Repository", "url", f"https://github.com/{args.github_handle.strip('/')}")
    elif not tmp.tmp_config.has_option("Repository", "url"):
        raise AttributeError("Parameter [Repository][url] must be provided either in config file or by --repo_url")

    if args.repo_local_path:
        tmp.tmp_config.set("Repository", "local_path", args.local_path)
    elif not tmp.tmp_config.has_option("Repository", "local_path"):
        tmp.tmp_config.set("Repository", "local_path", os.path.join(os.getcwd(), "analysed_repositories"))

    if args.development_mode:
        tmp.tmp_config.set("Analysis Settings", "development_mode", "True")

    if args.commit is not None:
        commit = args.commit[:7]
        tmp.tmp_config.set("Repository", "commit", commit)
    elif tmp.tmp_config.has_option("Repository", "commit"):
        commit = tmp.tmp_config.get("Repository", "commit")[:7]
        tmp.tmp_config.set("Repository", "commit", commit)

    perform_analysis()


if __name__ == '__main__':
    cli_invocation()
