#!/usr/bin/python3

import socket
from contextlib import contextmanager

from common import config

from .player import Player


@contextmanager
def connect_to_server(client):
    if not isinstance(client, Client):
        raise Exception(f"It's not a {Client.__name__} instance!")
    try:
        client.conn.connect(config.C_ADDRESS)
        client.player = Player(client.conn)
        client.player.login(auto_login=config.AUTO_LOGIN)
        yield
    finally:
        if client.conn:
            client.conn.close()


class Client:
    def __init__(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player = None

    def run(self):
        try:
            with connect_to_server(self):
                while self.player and self.player.in_game:
                    self.player.start_game()
        except Exception as e:
            print(e)
