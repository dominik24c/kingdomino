#!/usr/bin/python3
import socket
import sys
from contextlib import contextmanager

from common import config
from common.utils import encode
from .exceptions import *
from .game.game import Game
from .game.player import Player
from .dependencies import logger


def create_connection():
    logger.info(f'{config.SERVER} Start program')
    logger.info(f'{config.SERVER} Creating server...')
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sys.platform == "linux":
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(config.ADDRESS)
    except Exception as e:
        raise CreatingServerFailed(e)
    else:
        return server


@contextmanager
def openConnection(server):
    if not isinstance(server, Server):
        raise Exception(f"It's not {Server.__name__} instance!")
    try:
        server.listen()
        yield
    finally:
        conn = server.conn
        if conn:
            conn.close()


class Server(object):
    def __init__(self):
        self.conn = create_connection()
        self.game = Game()

    def listen(self):
        logger.info(f"{config.SERVER} Listening...")
        try:
            self.conn.listen(config.NUMBER_OF_PLAYERS)
        except Exception as e:
            raise ListeningServerFailed(e)

    def run(self):
        try:
            with openConnection(self):
                while self.game.inGame:
                    conn, addr = self.conn.accept()
                    logger.info(f"{config.SERVER} NEW PLAYER HAS JOINED.")
                    conn.send(encode(f'{config.S_CONNECT}'))

                    player = Player(conn, self.game, self.game.amountOfPlayers + 1)
                    self.game.addNewPlayer(player)
                    if len(self.game.players) == config.NUMBER_OF_PLAYERS:
                        self.game.startGame()
                        for player in self.game.players:
                            player.join()
                        logger.info('END GAME')
                    # break
        except KeyboardInterrupt:
            self.game.inGame = False
            logger.warn('Keyboard Interrupt')
        except Exception as e:
            logger.error(f'Error {e}')
            raise ConnectionServerFailed(e)

        logger.info(f'END PROGRAM')
