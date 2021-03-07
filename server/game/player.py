import threading
import socket
import logging
import time

from config import *
from exceptions.exceptions import EmptyMessage, NotPassedArgs, TooLongMessage
from game.base_player import BasePlayer
from game.board import Board


class Player(BasePlayer, threading.Thread):
    def __init__(self, conn, game, idPlayer, name=""):
        BasePlayer.__init__(self, conn, UTF8, BUFF_SIZE, idPlayer)
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('server_app')

        self.name = name
        self.game = game
        self.inGame = True
        self.puzzle = None
        self.isConnection = True
        self.numOfErrors = 0
        self.isYourMove = threading.Event()
        self.isYourMove.set()
        self.board = Board()
        self.isLogin = True

    def getPlayerInfo(self):
        return f'[PLAYER {self.idPlayer}] - '

    def getCommandAndArgs(self, msg):
        msgWithoutNewLine = msg.rstrip('\n')
        listOfMsg = msgWithoutNewLine.split(" ")
        utilizedList = list(filter(lambda char: char != "", listOfMsg))

        command = utilizedList[0]
        if len(utilizedList) == 1:
            args = []
        else:
            args = utilizedList[1:]
        return command, args

    def sendError(self):
        self.numOfErrors += 1
        self.sendMsg(f'{S_ERROR}\n')
        self.logger.error(f'{CLIENT} {self.getPlayerInfo()} {S_ERROR}\n')

    def handleMsg(self):
        try:
            msg = self.recvMsg()
            messages = msg.split("\n")
            messages = list(filter(None, messages))
            return messages
        except Exception as e:
            self.logger.error(str(e))

    def handleLogin(self, args):
        if len(args) == 1 and self.name == "":
            self.name = args[0]
            self.logger.info(
                f'{CLIENT} {self.getPlayerInfo()} Set nickname: {self.name}')
            self.sendMsg(f'{S_OK}\n')
            self.numOfErrors = 0
        else:
            self.logger.error(
                f'{CLIENT} {self.getPlayerInfo()} Cannot set nickname!')
            self.logger.error(
                f'{CLIENT} {self.getPlayerInfo()} Your args: {args}')
            self.sendError()

    def handleMove(self, args):
        if len(args) != 3:
            self.sendError()
        else:
            try:
                x = int(args[0])
                y = int(args[1])
                orientation = int(args[2])
            except Exception as e:
                self.sendError()
                return
            if self.game.legalMove(self, x=x, y=y, orientation=orientation):
                self.numOfErrors = 0
                self.logger.info(
                    f'{CLIENT} {self.getPlayerInfo()} {S_MOVE}: {self.idPlayer}')
            else:
                self.sendError()

    def handleChoose(self, args):
        if len(args) != 1:
            self.sendError()
        else:
            try:
                puzzle = int(args[0])
            except Exception as e:
                self.sendError()
                return
            if self.game.legalMove(self, puzzle):
                self.logger.info(
                    f'{CLIENT} {self.getPlayerInfo()} {S_CHOOSE}: {puzzle}')
                self.numOfErrors = 0
            else:
                self.sendError()

    def run(self):
        while self.isConnection and self.inGame:
            if self.isYourMove.isSet():
                # print('waiting for response')
                if self.isLogin:
                    self.isLogin = False
                    timeout = TIMEOUT_LOGIN
                else:
                    timeout = TIMEOUT

                try:
                    self.logger.info(
                        f'{CLIENT} {self.getPlayerInfo()} waiting for response')
                    self.conn.settimeout(timeout)
                    messages = self.handleMsg()
                    self.conn.settimeout(None)
                except IndexError:
                    self.sendError()
                except TypeError:
                    self.logger.error(
                        f'{CLIENT} {self.getPlayerInfo()} lost connection')
                    self.isConnection = False
                except Exception as e:
                    self.logger.error(
                        f'{CLIENT} {self.getPlayerInfo()} {str(e)}')
                    self.conn.close()

                if messages is not None and len(messages) > 0:
                    for m in messages:
                        try:
                            if len(m) >= MAX_LENGTH_OF_MSG:
                                raise TooLongMessage
                        except TooLongMessage:
                            self.logger.error(
                                f'{CLIENT} {self.getPlayerInfo()} Too Long message! Client {self.idPlayer} was kicked!')
                            self.isConnection = False

                        command, args = self.getCommandAndArgs(m)
                        self.logger.info(
                            f'{CLIENT} {self.getPlayerInfo()} {command} {args}')

                        if self.isConnection:
                            if command in ALLOWED_CLIENT_COMMANDS:
                                if command == S_LOGIN:
                                    self.handleLogin(args)
                                    # print(self.isYourMove.isSet())
                                    # self.isYourMove.clear()
                                    while self.game.waitUntilLoginPlayers.isSet():
                                        pass
                                elif command == S_CHOOSE:
                                    self.handleChoose(args)
                                elif command == S_MOVE:
                                    self.handleMove(args)
                                else:
                                    self.logger.warn(
                                        f"{CLIENT} {self.getPlayerInfo()} Unknown command")
                                    self.sendError()
                                command = None
                            else:
                                self.logger.warn(
                                    f"{CLIENT} {self.getPlayerInfo()} Not allowed command")
                                self.sendError()

                        if self.numOfErrors >= NUM_OF_ERRORS:
                            self.logger.error(
                                f'{CLIENT} {self.getPlayerInfo()} Too much errors from client. Client {self.idPlayer} was kicked!')
                            self.isConnection = False
                            break

                elif messages is not None and len(messages) == 0:
                    print('lost connection')
                    self.logger.error(
                        f'{CLIENT} {self.getPlayerInfo()} lost connection!')
                    self.isConnection = False

                elif messages is None:
                    print('timeout')
                    self.logger.error(
                        f'{CLIENT} {self.getPlayerInfo()} timeout!')
                    self.isConnection = False
