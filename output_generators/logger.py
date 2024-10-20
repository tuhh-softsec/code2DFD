"""Logger implemented here. Other methods call this one when writing messages to log to have a single logger."""

import os
import logging
from datetime import date, datetime

log_level = "DEBUG"

numeric_level = getattr(logging, log_level.upper(), 10)
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
LOG_PATH = os.path.join(os.getcwd(), 'code2DFD_output', 'logs', f"{date.today().strftime('%b-%d-%Y')}--{datetime.now().strftime('%H-%M-%S')}.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logger = logging.getLogger("tool")
logging.basicConfig(filename=LOG_PATH, level=numeric_level, format=LOG_FORMAT)


# Set log levels of all imported modules to ERROR
logging.getLogger("github").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib.request").setLevel(logging.ERROR)
logging.getLogger("os").setLevel(logging.ERROR)
logging.getLogger("json").setLevel(logging.ERROR)
logging.getLogger("yaml").setLevel(logging.ERROR)
logging.getLogger("io").setLevel(logging.ERROR)
logging.getLogger("Github").setLevel(logging.ERROR)
