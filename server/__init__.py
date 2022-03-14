#!/usr/bin/python3
from common import config
from common.logger import initLogger
from .server import Server


@initLogger(config.SERVER_DIR_LOGS, config.SERVER_PATH_TO_LOGS)
def runServer():
    server = Server()
    server.run()
