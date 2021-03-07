#!/usr/bin/python3

import socket

from config import *
from game.player import Player
from logger import Logger


class Client(object):
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player = None

    def run(self):
        try:
            self.client.connect(ADDRESS)
            print("Connection is succeed!")

            '''Comunication with server'''

            self.player = Player(self.client)
            self.player.loginToGame(auto_login=AUTO_LOGIN)
            while self.player.inGame:
                self.player.startGame()

        except Exception as e:
            print(e)
