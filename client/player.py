#!/usr/bin/python3

import random
import sys
import time

from common import config
from common.base_player import BasePlayer
from common.logger import log


def getCommands():
    username = None
    hacker_mode = None
    if len(sys.argv) > 1:
        minIndex = 1
        for i in range(minIndex, len(sys.argv)):
            result = sys.argv[i].split("=")
            if len(result) == 2:
                if result[0] == config.A_LOGIN:
                    username = result[1]
                elif result[0] == config.A_HACKER_MODE:
                    hacker_mode = result[1]
    return username, hacker_mode


class Player(BasePlayer):
    def __init__(self, conn):
        super().__init__(conn)
        username, hacker_mode = getCommands()
        if username is None:
            username = self.generateNickname(10)

        self.name = username
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
        self.maxReceivedMessage = random.randint(0, config.MAX_RECEIVED_MESSAGE)
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

    @log
    def loginToGame(self, logger, auto_login=True):
        msg = self.getResponse()
        if msg == config.S_CONNECT:
            if auto_login:
                command = f'{config.S_LOGIN} {self.name}'
            else:
                nickname = input()
                command = f'{config.S_LOGIN} {nickname}'
                # print(f'send Login')
            logger.info(f"{config.CLIENT} - {command}")
            self.sendMsg(f'{command}')
        else:
            logger.warn(f'{config.SERVER} - Unknown command - {msg}')

    def convertingMsg(self, msg):
        l = msg.strip().replace("\n", "").split(" ")
        if len(l) == 1:
            return l[0], None  # return command
        elif len(l) > 1:
            return l[0], l[1:]  # return command and args

    @log
    def startCommandHandler(self, msg, logger):
        logger.info(f'{config.SERVER} - START')
        _, args = self.convertingMsg(msg)
        self.id = args[0]
        numberOfPlayers = int(len(args[1:]) / 2)
        self.puzzles = args[1 + numberOfPlayers:]

    @log
    def yourChoiceCommandHandler(self, logger):
        logger.info(f'{config.CLIENT} - {config.S_CHOOSE} {self.puzzles[0]}')
        self.sendMsg(f'{config.S_CHOOSE} {self.puzzles[0]}')

    @log
    def playerChoiceCommandHandler(self, msg, logger):
        logger.info(f'{config.SERVER} - {msg}')
        _, args = self.convertingMsg(msg)
        self.puzzle = args[2]
        self.puzzles.remove(self.puzzle)

    @log
    def roundCommandHandler(self, msg, logger):
        print(f'{msg}')
        self.puzzles = []
        _, args = self.convertingMsg(msg)
        if args is None:
            logger.info(f'{config.SERVER} - {config.S_ROUND}')
        else:
            self.puzzles = args
            logger.info(f'{config.SERVER} - {config.S_ROUND} {" ".join(self.puzzles)}')

        # print(f'Puzzles {self.puzzles}')

    @log
    def yourMoveCommandHandler(self, logger):
        logger.info(f'{config.SERVER} - {config.S_YOUR_MOVE}')
        self.rounds += 1
        if self.rounds == 1:
            pass
        else:
            if self.rounds % 2 == 0:
                self.posX += 2
            else:
                self.posX -= 2
                self.posY += 1

        msg = f'{config.S_MOVE} {self.posX} {self.posY} {self.orientation}'
        self.sendMsg(f'{msg}')
        logger.info(f'{config.CLIENT} - {msg}')

    @log
    def moveCommandHandler(self, msg, logger):
        logger.info(f'{config.SERVER} - {msg}')
        _, args = self.convertingMsg(msg)
        self.playerMoves += 1

    @log
    def startGame(self, logger):
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
                    if self.hacker_mode == config.H_EXIT_DURING_GAME:
                        self.exitDuringGame()
                    elif self.hacker_mode == config.H_TIMEOUT:
                        self.timeoutDuringGame()

                    if msg.startswith(config.S_GAME_OVER_RESULTS):
                        response = msg.replace("\n", "")
                        logger.info(f'{config.SERVER} - {response}')
                        self.inGame = False

                    elif msg.startswith(config.S_START):
                        self.startCommandHandler(msg)

                    elif msg.startswith(config.S_YOUR_CHOICE):
                        if self.hacker_mode == config.H_EXIT_AFTER_CHOICE:
                            self.exitAfterYourChoice()

                        elif self.hacker_mode == config.H_SPAM:
                            self.sendLoginMessagesInfinity()

                        self.yourChoiceCommandHandler()

                    elif msg.startswith(config.S_PLAYER_CHOICE):
                        self.playerChoiceCommandHandler(msg)

                    elif msg.startswith(config.S_ROUND):
                        self.roundCommandHandler(msg)

                    elif msg.startswith(config.S_YOUR_MOVE):
                        self.yourMoveCommandHandler()

                    elif msg.startswith(config.S_PLAYER_MOVE):
                        self.moveCommandHandler(msg)

                    elif msg == config.S_OK:
                        logger.info(f'{config.SERVER} - {config.S_OK}')

                    elif msg == config.S_ERROR:
                        logger.info(f'{config.SERVER} - {config.S_ERROR}')

                    else:
                        # print(msg)
                        logger.warn(f'{config.SERVER} - Unknown command: {msg}')

    def timeoutDuringGame(self):
        if self.flagTimeoutDuringGame == self.rounds:
            time.sleep(5)
            sys.exit(1)

    def exitDuringGame(self):
        self.receivedMessage += 1
        if self.receivedMessage > config.MAX_RECEIVED_MESSAGE:
            sys.exit(1)

    def exitAfterYourChoice(self):
        if self.exitGameAfterYourChoice == self.rounds:
            sys.exit(1)

    def sendLoginMessagesInfinity(self):
        while True:
            command = f'{config.S_LOGIN} You have been hacked!'
            self.sendMsg(command)
