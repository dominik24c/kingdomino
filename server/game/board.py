from common import config
from .puzzles import PUZZLES


class BoardHandlerMixin:
    def generateBoard(self, maxPos):
        """
        :param int maxPos: max length of position
        :return [[None,None],[None,None]...]: generate board as two-dimensional array
        """
        board = []
        for i in range(2 * maxPos + 1):
            board.append([None] * (2 * maxPos + 1))
        return board

    def printBoard(self, fields):
        """helper method to print current state of players board"""
        for i, row in enumerate(fields):
            for j, item in enumerate(row):
                if item is not None:
                    print(f'Board[{i}][{j}]: {item}')


class Board(BoardHandlerMixin):
    def __init__(self):
        self.mid = 100
        self.maxPos = 100
        self.minPos = - self.mid
        self.fields = self.generateBoard(self.maxPos)
        self.points = 0
        self.diff = 100
        self.setCastle()

    def setCastle(self):
        """set castle on the middle position of board"""
        self.fields[self.mid][self.mid] = config.CASTLE

    def checkIsCorrectMove(self, x, y, orientation):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        :return boolean: return true if x,y are correct value on the board,
                two fields [x,y] and [x1,y1](it depends on the orientation) are empty
                and one of these field is adjacent of the puzzles on the board
        """
        flag = False
        # check position of player
        x1, y1 = self.getSecondPosOfPuzzle(x, y, orientation)
        if self.isCorrectPosition(x, y, orientation) and self.isCorrectPosition(x1, y1):
            x += self.diff
            x1 += self.diff
            y += self.diff
            y1 += self.diff

            if self.isEmptyField(x, y) and self.isEmptyField(x1, y1) and (
                    self.isNearOfThePuzzle(x, y) or self.isNearOfThePuzzle(x1, y1)):
                flag = True

        return flag

    def isEmptyField(self, x, y):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :return boolean: return false if field is equal None, otherwise it returns true
        """
        # print(f'[IS EMPTY] Field[{x}][{y}] = {self.fields[x][y]}')
        if self.fields[x][y] is None:
            return True
        else:
            return False

    def isCorrectPosition(self, x, y, orientation=0):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        :return boolean: return true if x, y and orientation have correct value
        """
        allowedOrientation = [0, 90, 180, 270]
        if (self.maxPos >= x >= self.minPos) and (
                self.maxPos >= y >= self.minPos) and orientation in allowedOrientation:
            return True
        return False

    def isNearOfThePuzzle(self, x, y):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :return boolean: returns true if a puzzle is adjacent to another one
        """
        positionsToCheck = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for position in positionsToCheck:
            posX = x + position[0]
            posY = y + position[1]
            # print(f'[IS NEAR] Field[{posX}][{posY}] = {self.fields[posX][posY]}')
            if self.fields[posX][posY] is not None:
                return True
        return False

    ###########################################################################
    def getSecondPosOfPuzzle(self, x, y, orientation=0):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        :return int, int: the coordinates of second position field, which depends on the orientation
        """
        x1 = x
        y1 = y
        if orientation == 0:
            x1 += 1
        elif orientation == 90:
            y1 += 1
        elif orientation == 180:
            x1 -= 1
        elif orientation == 270:
            y1 -= 1
        return x1, y1

    def addPuzzleToTheBoard(self, puzzle, x, y, orientation):
        """
        Add puzzle to the board, which takes two field
        :param str puzzle: it's key of PUZZLES dictionary
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        """
        # ('id player', 'number of puzzle')
        puzzles = PUZZLES[puzzle].split(" ")
        x += 100
        y += 100
        firstPartPuzzle = puzzles[0]
        secondPartPuzzle = puzzles[1]

        self.fields[x][y] = firstPartPuzzle
        x1, y1 = self.getSecondPosOfPuzzle(x, y, orientation)
        self.fields[x1][y1] = secondPartPuzzle
        # self.printBoard()

    def calculateResult(self):
        """
        :return int: total score of player
        """
        rows = len(self.fields)
        columns = len(self.fields[0])

        for i in range(0, rows):
            for j in range(0, columns):
                field, bonus = self.getValueAndBonus(self.fields[i][j])
                if bonus is None:
                    bonus = 0
                if field is not None:
                    res, b = self.searchField(field, i, j)
                    bonus += b
                    self.points = self.points + (res + 1) * (bonus + 1)
        return self.points

    def searchField(self, field, i, j):
        """
        :param str field: kind of the puzzle ex. g - grass, f - forest,
        :param int i: i coordinate of puzzle,
        :param int j: j coordinate of puzzle,
        :return int, int - amount of total adjacent specific type fields, total bonus
        """
        self.fields[i][j] = None
        bonus = 0
        arr = [0, 0, 0, 0]

        pointers = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for k in range(0, len(arr)):
            p = pointers[k]
            v, b = self.searchFieldRecursive(field, i + p[0], j + p[1])
            arr[k] += v
            bonus += b

        return sum(arr), bonus

    def searchFieldRecursive(self, field, i, j):
        """
        :param str field: kind of the puzzle ex. g - grass, f - forest,
        :param int i: i coordinate of puzzle,
        :param int j: j coordinate of puzzle,
        :return int, int: amount of current adjacent specific type fields, current bonus
        """
        val, b = self.getValueAndBonus(self.fields[i][j])
        bon = self.getBonus(b)
        if val == field:
            v, b = self.searchField(field, i, j)
            return v + 1, bon + self.getBonus(b)
        return 0, 0

    def getValueAndBonus(self, field):
        """
        :param  str or None field: it's one of part of puzzle example g, m3
        :return str value, int bonus
        :raises Exception for greater length than 2 for field
        """
        if field is None:
            return None, None
        elif len(field) == 1:
            value = field[0]
            bonus = None
        elif len(field) == 2:
            value = field[0]
            bonus = int(field[1])
        elif len(field) == len(config.CASTLE) and field == config.CASTLE:
            return None, None
        else:
            raise Exception("Incorrect value for field!")

        return value, bonus

    def getBonus(self, bonus):
        """
        :param int bonus: value of bonus
        :return int: value of bonus
        """
        if bonus is None:
            return 0
        return bonus
