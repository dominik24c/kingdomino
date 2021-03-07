#!/usr/bin/python3
from server import Server
from logger import Logger


def runServer():
    Logger()
    server = Server()
    server.run()


if __name__ == "__main__":
    runServer()
