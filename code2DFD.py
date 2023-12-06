#!/usr/bin/env python3
#
# Author: Simon Schneider, 2023
# Contact: simon.schneider@tuhh.de

import sys
import os
from configparser import ConfigParser
from datetime import datetime

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
    tmp.tmp_config.set("Repository", "path", str(path))

    local_path = "./analysed_repositories/" + ("/").join(path.split("/")[1:])
    tmp.tmp_config.set("Repository", "local_path", local_path)

    if not fi.repo_downloaded(local_path):
        fi.download_repo(path)

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
    now = datetime.now()
    start_time = now.strftime("%H:%M:%S")

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

    arguments = sys.argv
    invocation_command = "python3"
    for argument in arguments:
        invocation_command += " " + argument
    tmp.tmp_config.set("Repository", "invocation_command", invocation_command)

    if len(arguments) == 1:
        repo_path = tmp.tmp_config["Repository"]["path"]
        print("No repository given as parameter. \
                \n   You can provide the path as: > python3 code2dfd.py repository/path \
                \nAnalysing " + repo_path + " as specified in config/config.ini")
    elif len(arguments) == 2:
        repo_path = arguments[1]
        tmp.tmp_config.set("Repository", "path", repo_path)
    elif len(arguments) >2:
        print("Please specify the repository paths one by one.")
        return

    # Create analysed_repositories folder in case it doesn't exist yet (issue #2)
    os.makedirs(os.path.dirname("./analysed_repositories"), exist_ok=True)

    local_path = "./analysed_repositories/" + ("/").join(repo_path.split("/")[1:])
    tmp.tmp_config.set("Repository", "local_path", local_path)

    if not fi.repo_downloaded(local_path):
        fi.download_repo(repo_path)

    # calling the actual extraction
    dfd_extraction.perform_analysis()

    now = datetime.now()
    end_time = now.strftime("%H:%M:%S")

    print("\nStarted", start_time)
    print("Finished", end_time)


if __name__ == '__main__':
    main()
