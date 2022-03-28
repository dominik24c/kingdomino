import random
import threading
import time

from common import config
from common.logger import log
from server.utils import listToStr
from .puzzles import PUZZLES


class Game:
    def __init__(self):
        self.waitUntilLoginPlayers = threading.Event()
        self.waitUntilLoginPlayers.set()

        # variables used by player
        self.lock = threading.Lock()
        self.players = []
        self.allPlayers = []
        self.amountOfPlayers = 0
        self.inGame = True

        # variables to choosing puzzles by player
        self.isNewRound = False
        self.orderOfPlayers = []
        self.puzzles = list(PUZZLES.items())
        self.puzzlesOnRound = []
        self.currentPlayer = None
        self.rounds = 0

        # states
        self.drawingState = True
        self.playingState = False

        # variables used by board
        self.puzzlesInGame = []  # [(id,puzzle), ... ] //sorted
        self.puzzlesInGameTmp = []

    def toggleStateOfGame(self):
        self.drawingState, self.playingState = self.playingState, self.drawingState

    def drawPlayers(self):
        tmpPlayers = self.players.copy()
        random.shuffle(tmpPlayers)

        self.orderOfPlayers = [player.idPlayer for player in tmpPlayers]
        return self.orderOfPlayers[0]

    def setOrderOfPlayers(self):
        self.puzzlesInGameTmp.sort(key=lambda x: x[1])
        self.orderOfPlayers = [puzzle[0] for puzzle in self.puzzlesInGameTmp]
        self.puzzlesInGameTmp = []
        return self.orderOfPlayers[0]

    def removeItemPuzzlesInTmpList(self, id):
        index = None
        for i in range(len(self.puzzlesInGameTmp)):
            if self.puzzlesInGameTmp[i][0] == id:
                index = i
        if index is not None:
            self.puzzlesInGameTmp.pop(index)

    def drawPuzzles(self):
        # print(f'Rounds {self.rounds}')
        # print(f'{len(self.puzzles)}')
        if len(self.puzzles) > 0 and self.rounds < config.ROUNDS:
            self.puzzlesOnRound = []
            for i in range(config.NUMBER_OF_PLAYERS):
                index = random.randint(0, len(self.puzzles) - 1)
                puzzle = self.puzzles.pop(index)
                self.puzzlesOnRound.append(puzzle[0])
        elif self.rounds == config.ROUNDS:
            self.puzzlesOnRound = self.puzzlesInGameTmp.copy()
        else:
            self.puzzlesOnRound = []

    def drawNewRound(self):
        self.drawPuzzles()
        self.sendRound()
        self.rounds += 1

    def addNewPlayer(self, player):
        self.amountOfPlayers += 1
        self.players.append(player)

    def removePlayerById(self, idPlayer):
        for player in self.players:
            if player.idPlayer == idPlayer:
                self.players.remove(player)
                # print(f'Removed player-{idPlayer}')

    def getPlayerById(self, idPlayer):
        playerList = [player for player in self.players if player.idPlayer == idPlayer]
        if len(playerList) != 0:
            return playerList[0]

    def checkLogin(self):
        indexes = [index for index, player in enumerate(self.players) if player.name == '']
        for index in indexes:
            self.players.pop(index)

    def waitForLoginPlayers(self):
        start = time.time()
        end = time.time()
        flagLogin = False
        while (end - start) <= config.TIMEOUT_LOGIN and not flagLogin:
            flagLogin = True
            for player in self.players:
                if player.name == "":
                    flagLogin = False
                    break
            end = time.time()

    def changeCurrentPlayer(self):
        # print(f'current player {self.currentPlayer}')
        self.removeItemPuzzlesInTmpList(self.currentPlayer)
        self.removePlayerById(self.currentPlayer)
        if len(self.players) == 0:
            return
        elif self.drawingState:
            # print(f'in drawing state')
            self.orderOfPlayers.pop(0)
            if len(self.orderOfPlayers) == 0:
                # print(f'go to playing state')
                self.toggleStateOfGame()
                self.drawNewRound()
                self.currentPlayer = self.puzzlesInGame[0][0]
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourMove(self.getPlayerById(self.currentPlayer))
                self.puzzlesInGameTmp = self.puzzlesInGame.copy()
            else:
                # print('switch player to choosing puzzle')
                self.currentPlayer = self.orderOfPlayers[0]
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourChoice(self.getPlayerById(self.currentPlayer))

        elif self.playingState:
            # print('in playing state')
            self.puzzlesInGame.pop(0)
            if len(self.puzzlesInGame) == 0:
                # print('go to drawing state')
                self.currentPlayer = self.setOrderOfPlayers()
                self.toggleStateOfGame()
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourChoice(self.getPlayerById(self.currentPlayer))
            else:
                # print('switch player to moving your puzzle')
                self.currentPlayer = self.puzzlesInGame[0][0]
                self.sendYourMove(self.getPlayerById(self.currentPlayer))

    @log
    def sendStartGame(self, logger):
        self.currentPlayer = self.drawPlayers()
        self.drawPuzzles()
        for player in self.players:
            if player.idPlayer in self.orderOfPlayers:
                logger.info(
                    f'{config.SERVER} {config.S_START} {player.idPlayer} {listToStr(self.orderOfPlayers)} {listToStr(self.puzzlesOnRound)}')
                player.sendMsg(
                    f'{config.S_START} {player.idPlayer} {listToStr(self.orderOfPlayers)} {listToStr(self.puzzlesOnRound)}')

        self.sendYourChoice(self.getPlayerById(self.currentPlayer))
        self.rounds += 1

    @log
    def sendYourChoice(self, player, logger):
        if player is not None and player.idPlayer == self.orderOfPlayers[0]:
            player.isYourMove.set()
            player.sendMsg(f'{config.S_YOUR_CHOICE}')
            logger.info(
                f'{config.SERVER} SEND TO PLAYER {player.idPlayer} {config.S_YOUR_CHOICE}')
            return True
        return False

    def sendPlayerChoice(self, choosenPuzzle):
        for player in self.players:
            if self.currentPlayer != player.idPlayer and player.idPlayer in self.orderOfPlayers:
                player.sendMsg(f'{config.S_PLAYER_CHOICE} {self.currentPlayer} {choosenPuzzle}')

    @log
    def sendRound(self, logger):
        puzzles = ""
        if len(self.puzzlesOnRound) > 0 and self.rounds < config.ROUNDS:
            puzzles = listToStr(self.puzzlesOnRound)
        logger.info(f'{config.SERVER} {config.S_ROUND} {puzzles}')
        for player in self.players:
            player.sendMsg(f'{config.S_ROUND} {puzzles}')

    @log
    def sendYourMove(self, player, logger):
        if player.idPlayer == self.puzzlesInGame[0][0]:
            player.isYourMove.set()
            logger.info(f'{config.SERVER} SEND TO PLAYER {player.idPlayer} {config.S_YOUR_MOVE}')
            player.sendMsg(f'{config.S_YOUR_MOVE}')
            return True
        return False

    @log
    def sendPlayerMove(self, x, y, orientation, logger):
        logger.info(f'{config.SERVER} {config.S_PLAYER_MOVE} {self.currentPlayer} {x} {y} {orientation}')
        idPlayers = [idPlayer for idPlayer, puzzle in self.puzzlesInGame]
        for player in self.players:
            if self.currentPlayer != player.idPlayer and player.idPlayer in idPlayers:
                player.sendMsg(f'{config.S_PLAYER_MOVE} {self.currentPlayer} {x} {y} {orientation}')

    @log
    def sendGameOver(self, logger):
        results = [(player.idPlayer, player.board.calculateResult()) for player in self.allPlayers]
        results.sort(key=lambda x: x[1])
        results.reverse()
        stringResult = " ".join([f'{result[0]} {result[1]}' for result in results])

        for player in self.players:
            player.sendMsg(f'{config.S_GAME_OVER_RESULTS} {stringResult}')
            player.inGame = False

        logger.info(f'{config.SERVER} {config.S_GAME_OVER_RESULTS} {stringResult}')
        self.inGame = False

    def checkPuzzle(self, choosenPuzzle):
        return any([puzzle == choosenPuzzle for puzzle in self.puzzlesOnRound])

    def checkConnectionForPlayer(self):
        for player in self.players:
            if player is not None and not player.isConnection:
                return player.idPlayer
        return None

    @log
    def removePlayer(self, id, logger):
        self.removeItemPuzzlesInTmpList(id)
        self.removePlayerById(id)
        try:
            self.orderOfPlayers.remove(id)
        except ValueError:
            logger.error(f'Unexpected error: ValueError!')

        indexesToRemove = [index for index, puzzles in enumerate(self.puzzlesInGame) if puzzles[0] == id]
        indexesToRemove.reverse()

        for i in indexesToRemove:
            self.puzzlesInGame.pop(i)

    def unlockReceivingMessagesFromPlayers(self):
        for player in self.players:
            player.isYourMove.clear()
        self.waitUntilLoginPlayers.clear()

    @log
    def loginAndInitGame(self, logger):
        self.allPlayers = self.players.copy()
        for player in self.players:
            player.start()

        self.waitForLoginPlayers()
        self.checkLogin()
        self.unlockReceivingMessagesFromPlayers()
        logger.info(f'{config.SERVER} In Game')
        # self.logger.info(f'{config.SERVER} {self.players}')
        self.sendStartGame()

    @log
    def startGame(self, logger):
        self.loginAndInitGame()

        while self.inGame:
            idPlayer = self.checkConnectionForPlayer()
            if len(self.players) == 0:
                logger.info(f"{config.SERVER} EXIT GAME")
                self.inGame = False
            elif idPlayer is not None:
                logger.info(f'{config.SERVER} lost connection by player {idPlayer}')
                if self.currentPlayer == idPlayer:
                    # print('Remove current player')
                    self.changeCurrentPlayer()
                else:
                    # print('Remove player')
                    self.removePlayer(idPlayer)

    def legalMove(self, player, choosenPuzzle=0, x=0, y=0, orientation=0):
        flag = False
        with self.lock:
            # self.logger.info(f"{config.SERVER} Check legal Move")
            if self.drawingState and player.idPlayer == self.currentPlayer and self.checkPuzzle(choosenPuzzle):
                flag = True
                player.sendMsg(f'{config.S_OK}')
                player.isYourMove.clear()
                player.puzzle = choosenPuzzle
                self.sendPlayerChoice(choosenPuzzle)
                self.orderOfPlayers.pop(0)
                self.puzzlesOnRound.remove(choosenPuzzle)
                self.puzzlesInGame.append((player.idPlayer, choosenPuzzle))

                if len(self.orderOfPlayers) == 0:
                    self.drawingState = False
                    self.playingState = True
                    self.currentPlayer = self.puzzlesInGame[0][0]
                    self.drawNewRound()
                    self.sendYourMove(self.getPlayerById(self.currentPlayer))
                    self.puzzlesInGameTmp = self.puzzlesInGame.copy()
                else:
                    self.currentPlayer = self.orderOfPlayers[0]
                    for player in self.players:
                        self.sendYourChoice(player)

            elif self.playingState and player.idPlayer == self.currentPlayer and \
                    player.board.checkIsCorrectMove(x, y, orientation):
                flag = True
                player.sendMsg(f'{config.S_OK}')
                player.isYourMove.clear()
                self.puzzlesInGame.pop(0)
                player.board.addPuzzleToTheBoard(player.puzzle, x, y, orientation)

                if len(self.puzzlesInGame) == 0:
                    self.playingState = False
                    self.drawingState = True
                    # print(self.rounds)
                    if self.rounds <= config.ROUNDS:
                        self.currentPlayer = self.setOrderOfPlayers()
                        self.sendYourChoice(self.getPlayerById(self.currentPlayer))
                    else:
                        self.sendGameOver()

                else:
                    self.sendPlayerMove(x, y, orientation)
                    self.currentPlayer = self.puzzlesInGame[0][0]
                    # print(f'currentPlayer Move: {self.currentPlayer}')
                    for player in self.players:
                        self.sendYourMove(player)

        return flag
