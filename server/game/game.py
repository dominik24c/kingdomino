import threading
import random
import time
import logging

from config import *
from exceptions.exceptions import EmptyMessage, NotPassedArgs
from game.player import Player
from game.puzzles import PUZZLES


class Game(object):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('server_app')
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

    def drawPlayers(self):
        tmpPlayers = self.players.copy()
        random.shuffle(tmpPlayers)

        self.orderOfPlayers = []
        for player in tmpPlayers:
            self.orderOfPlayers.append(player.idPlayer)

        return self.orderOfPlayers[0]

    def setOrderOfPlayers(self):
        self.puzzlesInGameTmp.sort(key=lambda x: x[1])
        self.orderOfPlayers = []
        for element in self.puzzlesInGameTmp:
            self.orderOfPlayers.append(element[0])
        self.puzzlesInGameTmp = []

        # print(f'{self.orderOfPlayers}')
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
        if len(self.puzzles) > 0 and self.rounds < ROUNDS:
            self.puzzlesOnRound = []
            for i in range(NUMBER_OF_PLAYERS):
                index = random.randint(0, len(self.puzzles)-1)
                item = self.puzzles.pop(index)
                self.puzzlesOnRound.append(item[0])
        elif self.rounds == ROUNDS:
            self.puzzlesOnRound = self.puzzlesInGameTmp.copy()
        else:
            self.puzzlesOnRound = []

    def strList(self, listOfNumbers):
        tmpList = []
        for number in listOfNumbers:
            tmpList.append(str(number))
        return " ".join(tmpList)

    def drawNewRound(self):
        self.drawPuzzles()
        self.sendRound()
        self.rounds += 1

#############################################################################

    def addNewPlayer(self, player):
        self.amountOfPlayers += 1
        self.players.append(player)

    def removePlayerById(self, idPlayer):
        for player in self.players:
            if player.idPlayer == idPlayer:
                self.players.remove(player)
                # print(f'Removed player-{idPlayer}')

    def getPlayerById(self, idPlayer):
        playerList = [
            player for player in self.players if player.idPlayer == idPlayer]
        if len(playerList) != 0:
            return playerList[0]

# ###################################################################
    def checkLogin(self):
        indexes = []
        for index, player in enumerate(self.players):
            # print(player.name)
            if player.name == "":
                indexes.append(index)

        length = len(self.players)
        # print(length)
        for index in indexes:
            i = index - (length-len(self.players))
            self.players.pop(i)

    def waitForLoginPlayers(self):
        start = time.time()
        end = time.time()
        flagLogin = False
        while (end-start) <= TIMEOUT_LOGIN and not flagLogin:
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
                self.drawingState = False
                self.playingState = True
                self.drawNewRound()
                self.currentPlayer = self.puzzlesInGame[0][0]
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourMove(self.getPlayerById(self.currentPlayer))
                self.puzzlesInGameTmp = self.puzzlesInGame.copy()
            else:
                # print(f'switch player to choosing puzzle')
                self.currentPlayer = self.orderOfPlayers[0]
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourChoice(self.getPlayerById(self.currentPlayer))

        elif self.playingState:
            # print(f'in playing state')
            self.puzzlesInGame.pop(0)
            if len(self.puzzlesInGame) == 0:
                # print(f'go to drawing state')
                self.currentPlayer = self.setOrderOfPlayers()
                self.drawingState = True
                self.playingState = False
                # print(self.getPlayerById(self.currentPlayer))
                self.sendYourChoice(self.getPlayerById(self.currentPlayer))
            else:
                # print(f'switch player to moving your puzzle')
                self.currentPlayer = self.puzzlesInGame[0][0]
                self.sendYourMove(self.getPlayerById(self.currentPlayer))


######################################################################


    def sendStartGame(self):
        self.currentPlayer = self.drawPlayers()
        self.drawPuzzles()
        for player in self.players:
            if player.idPlayer in self.orderOfPlayers:
                self.logger.info(
                    f'{SERVER} {S_START} {player.idPlayer} {self.strList(self.orderOfPlayers)} {self.strList(self.puzzlesOnRound)}')
                player.sendMsg(
                    f'{S_START} {player.idPlayer} {self.strList(self.orderOfPlayers)} {self.strList(self.puzzlesOnRound)}\n')

        self.sendYourChoice(self.getPlayerById(self.currentPlayer))
        self.rounds += 1

    def sendYourChoice(self, player):
        if player is not None and player.idPlayer == self.orderOfPlayers[0]:
            player.isYourMove.set()
            player.sendMsg(f'{S_YOUR_CHOICE}\n')
            self.logger.info(
                f'{SERVER} SEND TO PLAYER {player.idPlayer} {S_YOUR_CHOICE}')
            return True
        return False

    def sendPlayerChoice(self, choosenPuzzle):
        for player in self.players:
            if self.currentPlayer != player.idPlayer and player.idPlayer in self.orderOfPlayers:
                player.sendMsg(
                    f'{S_PLAYER_CHOICE} {self.currentPlayer} {choosenPuzzle}\n')

    def sendRound(self):
        puzzles = ""
        if len(self.puzzlesOnRound) > 0 and self.rounds < ROUNDS:
            puzzles = " "+self.strList(self.puzzlesOnRound)
        self.logger.info(f'{SERVER} {S_ROUND}{puzzles}')
        for player in self.players:
            player.sendMsg(f'{S_ROUND}{puzzles}\n')

    def sendYourMove(self, player):
        if player.idPlayer == self.puzzlesInGame[0][0]:
            player.isYourMove.set()
            self.logger.info(
                f'{SERVER} SEND TO PLAYER {player.idPlayer} {S_YOUR_MOVE}')
            player.sendMsg(f'{S_YOUR_MOVE}\n')
            return True
        return False

    def sendPlayerMove(self, x, y, orientation):
        self.logger.info(
            f'{SERVER} {S_PLAYER_MOVE} {self.currentPlayer} {x} {y} {orientation}')
        idPlayers = [idPlayer for idPlayer, puzzle in self.puzzlesInGame]
        for player in self.players:
            if self.currentPlayer != player.idPlayer and player.idPlayer in idPlayers:
                player.sendMsg(
                    f'{S_PLAYER_MOVE} {self.currentPlayer} {x} {y} {orientation}\n')

    def sendGameOver(self):
        results = []
        for player in self.allPlayers:
            points = player.board.calculateResult()
            results.append((player.idPlayer, points))
        results.sort(key=lambda x: x[1])
        results.reverse()
        stringResult = ""
        for result in results:
            stringResult += str(result[0])+" "+str(result[1]) + " "
        stringResult = stringResult.strip()
        # print(stringResult)
        for player in self.players:
            player.sendMsg(f'{S_GAME_OVER_RESULTS} {stringResult}')

        for player in self.players:
            if player is not None:
                player.inGame = False
                # player.join()

        self.logger.info(f'{SERVER} {S_GAME_OVER_RESULTS} {stringResult}')
        self.inGame = False

#########################################################################################
    def checkPuzzle(self, choosenPuzzle):
        flag = False
        for puzzle in self.puzzlesOnRound:
            if puzzle == choosenPuzzle:
                flag = True
                break
        return flag

    def checkConnectionForPlayer(self):
        for player in self.players:
            if player is not None:
                if not player.isConnection:
                    return player.idPlayer
        return None

    def removePlayer(self, id):
        self.removeItemPuzzlesInTmpList(id)
        self.removePlayerById(id)
        try:
            self.orderOfPlayers.remove(id)
        except ValueError:
            self.logger.error(f'Unexpected error: ValueError!')

        index = 0
        indexesToRemove = []
        for puzzles in self.puzzlesInGame:
            if puzzles[0] == id:
                indexesToRemove.append(index)
            index += 1

        indexesToRemove.reverse()
        for i in indexesToRemove:
            self.puzzlesInGame.pop(i)

    def unlockReceivingMessagesFromPlayers(self):
        for player in self.players:
            player.isYourMove.clear()
        self.waitUntilLoginPlayers.clear()

    def loginAndInitGame(self):
        self.allPlayers = self.players.copy()
        for player in self.players:
            player.start()

        self.waitForLoginPlayers()
        self.checkLogin()
        self.unlockReceivingMessagesFromPlayers()
        self.logger.info(f'{SERVER} In Game')
        # self.logger.info(f'{SERVER} {self.players}')
        self.sendStartGame()

    def startGame(self):
        self.loginAndInitGame()

        while self.inGame:
            with self.lock:
                idPlayer = self.checkConnectionForPlayer()
                if len(self.players) == 0:
                    self.logger.info(f"{SERVER} EXIT GAME")
                    self.inGame = False
                elif idPlayer is not None:
                    # print("LOST CONNECTION")
                    self.logger.info(
                        f'{SERVER} lost connection by player {idPlayer}')
                    if self.currentPlayer == idPlayer:
                        # print('Remove current player')
                        self.changeCurrentPlayer()
                    else:
                        # print('Remove player')
                        self.removePlayer(idPlayer)

##################################################################

    def legalMove(self, player, choosenPuzzle=0, x=0, y=0, orientation=0):
        flag = False
        with self.lock:
            # self.logger.info(f"{SERVER} Check legal Move")
            if self.drawingState and player.idPlayer == self.currentPlayer and self.checkPuzzle(choosenPuzzle):
                flag = True
                player.sendMsg(f'{S_OK}\n')
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

            elif self.playingState and player.idPlayer == self.currentPlayer and player.board.checkIsCorrectMove(x, y, orientation):
                flag = True
                player.sendMsg(f'{S_OK}\n')
                player.isYourMove.clear()
                self.puzzlesInGame.pop(0)
                player.board.addPuzzleToTheBoard(
                    player.puzzle, x, y, orientation)

                if len(self.puzzlesInGame) == 0:
                    self.playingState = False
                    self.drawingState = True
                    # print(self.rounds)
                    if self.rounds <= ROUNDS:
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
