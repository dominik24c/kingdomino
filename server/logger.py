import logging
import os
from config import *


class Logger():
    def __init__(self):
        # create logs directory if not exist
        if not os.path.isdir(DIRECTORY_LOGS):
            os.mkdir(DIRECTORY_LOGS)
        # set logger
        self.logger = logging.getLogger('server_app')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(PATH_TO_LOGS)
        fh.setLevel(logging.DEBUG)
        format = '%(asctime)s %(message)s'
        formatter = logging.Formatter(format)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        logging.basicConfig(format=format)
