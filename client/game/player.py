#!/usr/bin/python3

import random
import os
import sys
import logging
import time

from config import *
from game.base_player import BasePlayer


def getCommands():
    # print(len(sys.argv))
    data = []
    username = None
    hacker_mode = None
    if len(sys.argv) > 1:
        minIndex = 1
        for i in range(minIndex, len(sys.argv)):
            result = sys.argv[i].split("=")
            if len(result) == 2:
                if result[0] == A_LOGIN:
                    username = result[1]
                elif result[0] == A_HACKER_MODE:
                    hacker_mode = result[1]
    return username, hacker_mode


class Player(BasePlayer):
    def __init__(self, conn):
        super().__init__(conn, UTF8, BUFF_SIZE)
        username, hacker_mode = getCommands()
        if username is None:
            username = self.generateNickname(10)

        self.name = username
        self.logger = logging.getLogger('client_app')
        self.id = 0
        self.inGame = True

        self.playerMoves = 0
        self.rounds = 0

        self.posX = 0
        self.posY = 1
        self.orientation = 0

        self.puzzles = []
        self.puzzle = None

        self.hacker_mode = hacker_mode
        self.receivedMessage = 0
        self.maxReceivedMessage = random.randint(0, MAX_RECEIVED_MESSAGE)
        self.exitGameAfterYourChoice = random.randint(2, 10)
        self.flagTimeoutDuringGame = random.randint(2, 10)

    def generateNickname(self, size):
        start = ord("a")
        end = ord("z")
        nickname = ""
        for _ in range(size):
            decAsciiSign = random.randint(start, end)
            nickname += chr(decAsciiSign)

        return nickname

    def getResponse(self):
        msg = self.recvMsg()
        msg = msg.replace("\n", '')
        return msg

    def loginToGame(self, auto_login=True):
        msg = self.getResponse()
        if msg == S_CONNECT:
            if auto_login:
                command = f'{S_LOGIN} {self.name}'
            else:
                nickname = input()
                command = f'{S_LOGIN} {nickname}'
                # print(f'send Login')
            self.logger.info(f"{CLIENT} - {command}")
            self.sendMsg(f'{command}\n')
        else:
            self.logger.warn(f'{SERVER} - Unknown command - {msg}')

    def convertingMsg(self, msg):
        l = msg.strip().replace("\n", "").split(" ")
        if len(l) == 1:
            return l[0], None  # return command
        elif len(l) > 1:
            return l[0], l[1:]  # return command and args

    def handleStartCommand(self, msg):
        self.logger.info(f'{SERVER} - START')
        _, args = self.convertingMsg(msg)
        self.id = args[0]
        numberOfPlayers = int(len(args[1:])/2)
        self.puzzles = args[1+numberOfPlayers:]

    # answer from server
    def handleYourChoiceCommand(self, msg):
        self.logger.info(f'{CLIENT} - {S_CHOOSE} {self.puzzles[0]}')
        self.sendMsg(f'{S_CHOOSE} {self.puzzles[0]}\n')

    def handlePlayerChoiceCommand(self, msg):
        self.logger.info(f'{SERVER} - {msg}')
        _, args = self.convertingMsg(msg)
        self.puzzle = args[2]
        self.puzzles.remove(self.puzzle)

    def handleRoundCommand(self, msg):
        print(f'{msg}')
        self.puzzles = []
        _, args = self.convertingMsg(msg)
        if args is None:
            self.logger.info(f'{SERVER} - {S_ROUND}')
        else:
            self.puzzles = args
            self.logger.info(f'{SERVER} - {S_ROUND} {" ".join(self.puzzles)}')

        # print(f'Puzzles {self.puzzles}')

    def handleYourMoveCommand(self, msg):
        self.logger.info(f'{SERVER} - {S_YOUR_MOVE}')
        self.rounds += 1
        if self.rounds == 1:
            pass
        else:
            if self.rounds % 2 == 0:
                self.posX += 2
            else:
                self.posX -= 2
                self.posY += 1

        msg = f'{S_MOVE} {self.posX} {self.posY} {self.orientation}'
        self.sendMsg(f'{msg}\n')
        self.logger.info(f'{CLIENT} - {msg}')

    def handleMoveCommand(self, msg):
        self.logger.info(f'{SERVER} - {msg}')
        _, args = self.convertingMsg(msg)
        self.playerMoves += 1

    def startGame(self):
        while self.inGame:
            messages = self.recvMsg()
            # print(messages)
            if messages == "":
                self.inGame = False
            else:
                listOfMessages = messages.split("\n")
                listOfMessages = [m for m in listOfMessages if m != ""]
                # print(listOfMessages)
                for msg in listOfMessages:
                    if self.hacker_mode == H_EXIT_DURING_GAME:
                        self.exitDuringGame()
                    elif self.hacker_mode == H_TIMEOUT:
                        self.timeoutDuringGame()

                    if msg.startswith(S_GAME_OVER_RESULTS):
                        response = msg.replace("\n", "")
                        self.logger.info(f'{SERVER} - {response}')
                        self.inGame = False

                    elif msg.startswith(S_START):
                        self.handleStartCommand(msg)

                    elif msg.startswith(S_YOUR_CHOICE):
                        if self.hacker_mode == H_EXIT_AFTER_CHOICE:
                            self.exitAfterYourChoice()

                        elif self.hacker_mode == H_SPAM:
                            self.sendLoginMessagesInfinity()

                        self.handleYourChoiceCommand(msg)

                    elif msg.startswith(S_PLAYER_CHOICE):
                        self.handlePlayerChoiceCommand(msg)

                    elif msg.startswith(S_ROUND):
                        self.handleRoundCommand(msg)

                    elif msg.startswith(S_YOUR_MOVE):
                        self.handleYourMoveCommand(msg)

                    elif msg.startswith(S_PLAYER_MOVE):
                        self.handleMoveCommand(msg)

                    elif msg == S_OK:
                        self.logger.info(f'{SERVER} - {S_OK}')

                    elif msg == S_ERROR:
                        self.logger.info(f'{SERVER} - {S_ERROR}')

                    else:
                        # print(msg)
                        self.logger.warn(f'{SERVER} - Unknown command: {msg}')

    def timeoutDuringGame(self):
        if self.flagTimeoutDuringGame == self.rounds:
            time.sleep(5)
            sys.exit(1)

    def exitDuringGame(self):
        self.receivedMessage += 1
        if self.receivedMessage > MAX_RECEIVED_MESSAGE:
            sys.exit(1)

    def exitAfterYourChoice(self):
        if self.exitGameAfterYourChoice == self.rounds:
            sys.exit(1)

    def sendLoginMessagesInfinity(self):
        while True:
            command = f'{S_LOGIN} You have been hacked!\n'
            self.sendMsg(command)
