"""Logger implemented here. Other methods call this one when writing messages to log to have a single logger."""

import os
import logging
from datetime import date, datetime

log_level = "DEBUG"

numeric_level = getattr(logging, log_level.upper(), 10)
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
LOG_PATH = "./output/logs/"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

#filename = "./output/logs/test.log"
file = LOG_PATH + date.today().strftime("%b-%d-%Y") + "--" + datetime.now().strftime("%H-%M-%S") + ".log"
logger = logging.getLogger("tool")
logging.basicConfig(filename = file, level = numeric_level, format = LOG_FORMAT)


# Set log levels of all imported modules to ERROR
logging.getLogger("github").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib.request").setLevel(logging.ERROR)
logging.getLogger("os").setLevel(logging.ERROR)
logging.getLogger("json").setLevel(logging.ERROR)
logging.getLogger("yaml").setLevel(logging.ERROR)
logging.getLogger("io").setLevel(logging.ERROR)
logging.getLogger("Github").setLevel(logging.ERROR)


def write_log_message(message: str, level: str) -> None:
    """Writes passed message as passed level to log file"""
    level = str(level)
    message = str(message)
    eval("logger." + level + "(message)")
