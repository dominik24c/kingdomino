#!/usr/bin/python3
import sys
import socket
import threading
import logging

from config import *
from exceptions.exceptions import *
from game.game import Player, Game


class Server(object):
    def __init__(self):
        self.logger = logging.getLogger('server_app')
        self.logger.info(f'{SERVER} Start program')
        self.logger.info(f'{SERVER} Creating server...')
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sys.platform == "linux":
                self.server.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(ADDRESS)
        except Exception as e:
            raise CreatingServerFailed(e)
        self.game = Game()

    def listen(self):
        self.logger.info(f"{SERVER} Listening...")
        try:
            self.server.listen(NUMBER_OF_PLAYERS)
        except Exception as e:
            raise ListeningServerFailed(e)

    def run(self):
        self.listen()
        try:
            while self.game.inGame:
                conn, addr = self.server.accept()
                self.logger.info(f"{SERVER} NEW PLAYER HAS JOINED.")
                connectText = f'{S_CONNECT}\n'.encode(UTF8)
                conn.send(connectText)

                player = Player(conn, self.game, self.game.amountOfPlayers+1)
                self.game.addNewPlayer(player)
                if len(self.game.players) == NUMBER_OF_PLAYERS:
                    self.game.startGame()
                    for player in self.game.players:
                        player.join()
                    self.logger.info('END GAME')
                    # break
        except KeyboardInterrupt:
            self.game.inGame = False
            self.logger.warn('Interrupted')
        except Exception as e:
            self.logger.error(f'Error {e}')
            raise ConnectionServerFailed(e)
        finally:
            if self.server:
                self.server.close()

        self.logger.info(f'END PROGRAM')
