import threading

from common import config
from common.base_player import BasePlayer
from common.logger import log
from .board import Board
from ..utils import getCommandAndArgsForPlayer


class Player(BasePlayer, threading.Thread):
    def __init__(self, conn, game, idPlayer, name=""):
        BasePlayer.__init__(self, conn)
        threading.Thread.__init__(self)

        self.name = name
        self.game = game
        self.inGame = True
        self.puzzle = None
        self.isConnection = True
        self.isYourMove = threading.Event()
        self.isYourMove.set()
        self.board = Board()
        self.isLogin = True
        self.idPlayer = idPlayer
        self.numOfErrors = 0

    @log
    def sendMsg(self, msg, logger):
        try:
            super().sendMsg(msg)
        except Exception:
            m = msg.replace('\n', '')
            logger.error(f'{config.CLIENT} Connection lost! {self.idPlayer}, cannot send: {m}')
            self.isConnection = False

    def getPlayerInfo(self):
        return f'[PLAYER {self.idPlayer}] - '

    @log
    def sendError(self, logger):
        self.numOfErrors += 1
        self.sendMsg(f'{config.S_ERROR}')
        logger.error(f'{config.CLIENT} {self.getPlayerInfo()} {config.S_ERROR}')

    def messageHandler(self):
        msg = self.recvMsg()
        return [m for m in msg.split("\n") if m != '']

    @log
    def loginHandler(self, args, logger):
        if len(args) == 1 and self.name == "":
            self.name = args[0]
            logger.info(f'{config.CLIENT} {self.getPlayerInfo()} Set nickname: {self.name}')
            self.sendMsg(f'{config.S_OK}')
            self.numOfErrors = 0
        else:
            logger.error(f'{config.CLIENT} {self.getPlayerInfo()} Cannot set nickname!')
            logger.error(f'{config.CLIENT} {self.getPlayerInfo()} Your args: {args}')
            self.sendError()

    @log
    def moveHandler(self, args, logger):
        try:
            if len(args) != 3:
                raise Exception
            x, y, orientation = int(args[0]), int(args[1]), int(args[2])
            if self.game.legalMove(self, x=x, y=y, orientation=orientation):
                self.numOfErrors = 0
                logger.info(f'{config.CLIENT} {self.getPlayerInfo()} {config.S_MOVE}: {self.idPlayer}')
            else:
                self.sendError()
        except Exception as e:
            self.sendError()

    @log
    def chooseHandler(self, args, logger):
        try:
            if len(args) != 1:
                raise Exception
            puzzle = int(args[0])
            if self.game.legalMove(self, puzzle):
                logger.info(f'{config.CLIENT} {self.getPlayerInfo()} {config.S_CHOOSE}: {puzzle}')
                self.numOfErrors = 0
            else:
                self.sendError()
        except Exception as e:
            self.sendError()

    def getTimeout(self):
        if self.isLogin:
            self.isLogin = False
            timeout = config.TIMEOUT_LOGIN
        else:
            timeout = config.TIMEOUT
        return timeout

    @log
    def run(self, logger):
        messages = None
        while self.isConnection and self.inGame:
            if self.isYourMove.is_set():
                # print('waiting for response')
                timeout = self.getTimeout()
                try:
                    logger.info(f'{config.CLIENT} {self.getPlayerInfo()} waiting for response')
                    self.conn.settimeout(timeout)
                    messages = self.messageHandler()
                    self.conn.settimeout(None)
                except IndexError:
                    self.sendError()
                except TypeError:
                    logger.error(f'{config.CLIENT} {self.getPlayerInfo()} lost connection')
                    self.isConnection = False
                except TimeoutError as e:
                    logger.error(f'{config.CLIENT} {self.getPlayerInfo()} timeout!')
                    self.isConnection = False
                except Exception as e:
                    print(f'{type(e).__name__} exception')
                    logger.error(f'{config.CLIENT} {self.getPlayerInfo()} {e}')
                    self.conn.close()

                if messages is not None and len(messages) > 0:
                    for m in messages:
                        if len(m) >= config.MAX_LENGTH_OF_MSG:
                            logger.error(
                                f'{config.CLIENT} {self.getPlayerInfo()} Too Long message! Client {self.idPlayer} was '
                                f'kicked!')
                            self.isConnection = False

                        command, args = getCommandAndArgsForPlayer(m)
                        logger.info(f'{config.CLIENT} {self.getPlayerInfo()} {command} {args}')

                        if self.isConnection:
                            if command in config.ALLOWED_CLIENT_COMMANDS:
                                if command == config.S_LOGIN:
                                    self.loginHandler(args)
                                    # print(self.isYourMove.isSet())
                                    # self.isYourMove.clear()
                                    while self.game.waitUntilLoginPlayers.is_set():
                                        pass
                                elif command == config.S_CHOOSE:
                                    self.chooseHandler(args)
                                elif command == config.S_MOVE:
                                    self.moveHandler(args)
                                else:
                                    logger.warn(
                                        f"{config.CLIENT} {self.getPlayerInfo()} Unknown command")
                                    self.sendError()
                            else:
                                logger.warn(
                                    f"{config.CLIENT} {self.getPlayerInfo()} Not allowed command")
                                self.sendError()

                        if self.numOfErrors >= config.NUM_OF_ERRORS:
                            logger.error(
                                f'{config.CLIENT} {self.getPlayerInfo()} Too much errors from client. '
                                f'Client {self.idPlayer} was kicked!')
                            self.isConnection = False
                            break

                elif messages is not None and len(messages) == 0:
                    logger.error(f'{config.CLIENT} {self.getPlayerInfo()} lost connection!')
                    self.isConnection = False
