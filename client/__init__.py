#!/usr/bin/python3
from common import config
from common.logger import initLogger
from .client import Client


@initLogger(config.CLIENT_DIR_LOGS, config.CLIENT_PATH_TO_LOGS)
def runClient():
    client = Client()
    client.run()
