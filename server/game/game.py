import random
import threading
import time

from common import config
from server.utils import list_to_str

from ..dependencies import logger
from .puzzles import PUZZLES


class Game:
    def __init__(self):
        self.wait_for_players = threading.Event()
        self.wait_for_players.set()

        # variables used by player
        self.lock = threading.Lock()
        self.players = []
        self.allPlayers = []
        self.amountOfPlayers = 0
        self.in_game = True

        # variables to choosing puzzles by player
        self.is_new_round = False
        self.orderOfPlayers = []
        self.puzzles = list(PUZZLES.items())
        self.puzzlesOnRound = []
        self.current_player = None
        self.rounds = 0

        # states
        self.drawingState = True
        self.playingState = False

        # variables used by board
        self.puzzles_in_game = []  # [(id,puzzle), ... ] //sorted
        self.puzzles_in_game_tmp = []

    def toggleStateOfGame(self):
        self.drawingState, self.playingState = (
            self.playingState,
            self.drawingState,
        )

    def draw_player(self):
        tmpPlayers = self.players.copy()
        random.shuffle(tmpPlayers)

        self.orderOfPlayers = [player.unique_id for player in tmpPlayers]
        return self.orderOfPlayers[0]

    def set_order_of_players(self):
        self.orderOfPlayers = [
            puzzle[0]
            for puzzle in sorted(self.puzzles_in_game_tmp, key=lambda x: x[1])
        ]
        self.puzzles_in_game_tmp.clear()
        return self.orderOfPlayers[0]

    def removeItemPuzzlesInTmpList(self, id):
        index = None
        for i in range(len(self.puzzles_in_game_tmp)):
            if self.puzzles_in_game_tmp[i][0] == id:
                index = i
        if index is not None:
            self.puzzles_in_game_tmp.pop(index)

    def drawPuzzles(self):
        # print(f'Rounds {self.rounds}')
        # print(f'{len(self.puzzles)}')
        if len(self.puzzles) > 0 and self.rounds < config.ROUNDS:
            self.puzzlesOnRound = []
            for _ in range(config.NUMBER_OF_PLAYERS):
                index = random.randint(0, len(self.puzzles) - 1)
                puzzle = self.puzzles.pop(index)
                self.puzzlesOnRound.append(puzzle[0])
        elif self.rounds == config.ROUNDS:
            self.puzzlesOnRound = self.puzzles_in_game_tmp.copy()
        else:
            self.puzzlesOnRound = []

    def drawNewRound(self):
        self.drawPuzzles()
        self.sendRound()
        self.rounds += 1

    def addNewPlayer(self, player):
        self.amountOfPlayers += 1
        self.players.append(player)

    def removePlayerById(self, unique_id):
        for player in self.players:
            if player.unique_id == unique_id:
                self.players.remove(player)
                # print(f'Removed player-{unique_id}')

    def getPlayerById(self, unique_id):
        for player in self.players:
            if player.unique_id == unique_id:
                return player

    def checkLogin(self):
        self.players = [player for player in self.players if player.name]

    def waitForLoginPlayers(self):
        start = time.time()
        while time.time() - start <= config.TIMEOUT_LOGIN:
            if all(player.name != "" for player in self.players):
                return  # All players are logged in
        time.sleep(0.1)

    def changeCurrentPlayer(self):
        # print(f'current player {self.current_player}')
        self.removeItemPuzzlesInTmpList(self.current_player)
        self.removePlayerById(self.current_player)
        if len(self.players) == 0:
            return
        elif self.drawingState:
            # print(f'in drawing state')
            self.orderOfPlayers.pop(0)
            if len(self.orderOfPlayers) == 0:
                # print(f'go to playing state')
                self.toggleStateOfGame()
                self.drawNewRound()
                self.current_player = self.puzzles_in_game[0][0]
                # print(self.getPlayerById(self.current_player))
                self.sendYourMove(self.getPlayerById(self.current_player))
                self.puzzles_in_game_tmp = self.puzzles_in_game.copy()
            else:
                # print('switch player to choosing puzzle')
                self.current_player = self.orderOfPlayers[0]
                # print(self.getPlayerById(self.current_player))
                self.sendYourChoice(self.getPlayerById(self.current_player))

        elif self.playingState:
            # print('in playing state')
            self.puzzles_in_game.pop(0)
            if len(self.puzzles_in_game) == 0:
                # print('go to drawing state')
                self.current_player = self.set_order_of_players()
                self.toggleStateOfGame()
                # print(self.getPlayerById(self.current_player))
                self.sendYourChoice(self.getPlayerById(self.current_player))
            else:
                # print('switch player to moving your puzzle')
                self.current_player = self.puzzles_in_game[0][0]
                self.sendYourMove(self.getPlayerById(self.current_player))

    def sendStartGame(self):
        self.current_player = self.draw_player()
        self.drawPuzzles()
        for player in self.players:
            if player.unique_id in self.orderOfPlayers:
                logger.info(
                    f"{config.SERVER} {config.S_START} {player.unique_id} \
                        {list_to_str(self.orderOfPlayers)} \
                            {list_to_str(self.puzzlesOnRound)}"
                )
                player.send_msg(
                    f"{config.S_START} {player.unique_id} \
                        {list_to_str(self.orderOfPlayers)} \
                            {list_to_str(self.puzzlesOnRound)}"
                )

        self.sendYourChoice(self.getPlayerById(self.current_player))
        self.rounds += 1

    def sendYourChoice(self, player):
        if player is not None and player.unique_id == self.orderOfPlayers[0]:
            player.your_turn.set()
            player.send_msg(f"{config.S_YOUR_CHOICE}")
            logger.info(
                f"{config.SERVER} SEND TO PLAYER \
                    {player.unique_id} {config.S_YOUR_CHOICE}"
            )
            return True
        return False

    def sendPlayerChoice(self, choosenPuzzle):
        for player in self.players:
            if (
                self.current_player != player.unique_id
                and player.unique_id in self.orderOfPlayers
            ):
                player.send_msg(
                    f"{config.S_PLAYER_CHOICE} \
                        {self.current_player} {choosenPuzzle}"
                )

    def sendRound(self):
        puzzles = ""
        if len(self.puzzlesOnRound) > 0 and self.rounds < config.ROUNDS:
            puzzles = list_to_str(self.puzzlesOnRound)
        logger.info(f"{config.SERVER} {config.S_ROUND} {puzzles}")
        for player in self.players:
            player.send_msg(f"{config.S_ROUND} {puzzles}")

    def sendYourMove(self, player):
        if player.unique_id == self.puzzles_in_game[0][0]:
            player.your_turn.set()
            logger.info(
                f"{config.SERVER} SEND TO PLAYER \
                    {player.unique_id} {config.S_YOUR_MOVE}"
            )
            player.send_msg(f"{config.S_YOUR_MOVE}")
            return True
        return False

    def sendPlayerMove(self, x, y, orientation):
        logger.info(
            f"{config.SERVER} {config.S_PLAYER_MOVE} {self.current_player}\
                  {x} {y} {orientation}"
        )
        unique_ids = [unique_id for unique_id, puzzle in self.puzzles_in_game]
        for player in self.players:
            if (
                self.current_player != player.unique_id
                and player.unique_id in unique_ids
            ):
                player.send_msg(
                    f"{config.S_PLAYER_MOVE} {self.current_player}\
                          {x} {y} {orientation}"
                )

    def sendGameOver(self):
        results = [
            (player.unique_id, player.board.calculate_result())
            for player in self.allPlayers
        ]
        results.sort(key=lambda x: x[1])
        results.reverse()
        stringResult = " ".join(
            [f"{result[0]} {result[1]}" for result in results]
        )

        for player in self.players:
            player.send_msg(f"{config.S_GAME_OVER_RESULTS} {stringResult}")
            player.in_game = False

        logger.info(
            f"{config.SERVER} {config.S_GAME_OVER_RESULTS} {stringResult}"
        )
        self.in_game = False

    def checkPuzzle(self, choosenPuzzle):
        return any([puzzle == choosenPuzzle for puzzle in self.puzzlesOnRound])

    def checkConnectionForPlayer(self):
        for player in self.players:
            if player is not None and not player.is_connection:
                return player.unique_id
        return None

    def removePlayer(self, id):
        self.removeItemPuzzlesInTmpList(id)
        self.removePlayerById(id)
        try:
            self.orderOfPlayers.remove(id)
        except ValueError:
            logger.error("Unexpected error: ValueError!")

        indexesToRemove = [
            index
            for index, puzzles in enumerate(self.puzzles_in_game)
            if puzzles[0] == id
        ]
        indexesToRemove.reverse()

        for i in indexesToRemove:
            self.puzzles_in_game.pop(i)

    def unlockReceivingMessagesFromPlayers(self):
        for player in self.players:
            player.your_turn.clear()
        self.wait_for_players.clear()

    def loginAndInitGame(self):
        self.allPlayers = self.players.copy()
        for player in self.players:
            player.start()

        self.waitForLoginPlayers()
        self.checkLogin()
        self.unlockReceivingMessagesFromPlayers()
        logger.info(f"{config.SERVER} In Game")
        # self.logger.info(f'{config.SERVER} {self.players}')
        self.sendStartGame()

    def startGame(self):
        self.loginAndInitGame()

        while self.in_game:
            unique_id = self.checkConnectionForPlayer()
            if len(self.players) == 0:
                logger.info(f"{config.SERVER} EXIT GAME")
                self.in_game = False
            elif unique_id is not None:
                logger.info(
                    f"{config.SERVER} lost connection by player {unique_id}"
                )
                if self.current_player == unique_id:
                    # print('Remove current player')
                    self.changeCurrentPlayer()
                else:
                    # print('Remove player')
                    self.removePlayer(unique_id)

    def legalMove(self, player, chosenPuzzle=0, x=0, y=0, orientation=0):
        flag = False
        with self.lock:
            # self.logger.info(f"{config.SERVER} Check legal Move")
            if (
                self.drawingState
                and player.unique_id == self.current_player
                and self.checkPuzzle(chosenPuzzle)
            ):
                flag = True
                player.send_msg(f"{config.S_OK}")
                player.your_turn.clear()
                player.puzzle = chosenPuzzle
                self.sendPlayerChoice(chosenPuzzle)
                self.orderOfPlayers.pop(0)
                self.puzzlesOnRound.remove(chosenPuzzle)
                self.puzzles_in_game.append((player.unique_id, chosenPuzzle))

                if len(self.orderOfPlayers) == 0:
                    self.drawingState = False
                    self.playingState = True
                    self.current_player = self.puzzles_in_game[0][0]
                    self.drawNewRound()
                    self.sendYourMove(self.getPlayerById(self.current_player))
                    self.puzzles_in_game_tmp = self.puzzles_in_game.copy()
                else:
                    self.current_player = self.orderOfPlayers[0]
                    for player in self.players:
                        self.sendYourChoice(player)

            elif (
                self.playingState
                and player.unique_id == self.current_player
                and player.board.check_is_correct_move(x, y, orientation)
            ):
                flag = True
                player.send_msg(f"{config.S_OK}")
                player.your_turn.clear()
                self.puzzles_in_game.pop(0)
                player.board.add_puzzle_to_the_board(
                    player.puzzle, x, y, orientation
                )

                if len(self.puzzles_in_game) == 0:
                    self.playingState = False
                    self.drawingState = True
                    # print(self.rounds)
                    if self.rounds <= config.ROUNDS:
                        self.current_player = self.set_order_of_players()
                        self.sendYourChoice(
                            self.getPlayerById(self.current_player)
                        )
                    else:
                        self.sendGameOver()

                else:
                    self.sendPlayerMove(x, y, orientation)
                    self.current_player = self.puzzles_in_game[0][0]
                    # print(f'currentPlayer Move: {self.current_player}')
                    for player in self.players:
                        self.sendYourMove(player)

        return flag
