import logging
from include.constants import *

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s %(funcName)s \t %(message)s')

# https://docs.python.org/3/library/logging.html#logging.Formatter

file_handler = logging.FileHandler(f"{LOGS_PATH}")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s \t %(funcName)s \t %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(file_handler)

# logging machine:
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)