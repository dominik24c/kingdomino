#!/usr/bin/python3
import sys

from client import Client
from logger import Logger

def runClient():
    Logger()
    client = Client()
    client.run()


if __name__ == "__main__":
    runClient()
