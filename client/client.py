#!/usr/bin/python3

import socket
from contextlib import contextmanager

from common import config
from .player import Player


@contextmanager
def connectToServer(client):
    if not isinstance(client, Client):
        raise Exception(f"It's not {Client.__name__} instance!")
    try:
        client.conn.connect(config.C_ADDRESS)
        client.player = Player(client.conn)
        client.player.loginToGame(auto_login=config.AUTO_LOGIN)
        yield
    finally:
        conn = client.conn
        if conn:
            conn.close()


class Client:
    def __init__(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player = None

    def run(self):
        try:
            with connectToServer(self):
                while self.player.inGame:
                    self.player.startGame()

        except Exception as e:
            print(e)
