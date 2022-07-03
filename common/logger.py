import logging
import os
from functools import wraps

from . import config


def createLogger(dirLogs, fullPathToLogs):
    if not os.path.isdir(fullPathToLogs):
        os.makedirs(dirLogs, exist_ok=True)
        # set logger
    logger = logging.getLogger(config.LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(fullPathToLogs)
    fh.setLevel(logging.DEBUG)
    format = '%(asctime)s %(message)s'
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logging.basicConfig(format=format)
    return logger