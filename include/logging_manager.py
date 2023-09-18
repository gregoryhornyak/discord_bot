import logging
from include.constants import *

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(funcName)s] - %(levelname)s : %(message)s')

# https://docs.python.org/3/library/logging.html#logging.Formatter

file_handler = logging.FileHandler(f"{LOGS_PATH}botlogs.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(file_handler)

# logging machine:
logger = logging.getLogger(__name__)