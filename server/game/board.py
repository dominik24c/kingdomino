from common import config
from .puzzles import PUZZLES


class BoardHandlerMixin:
    def generate_board(self, max_position):
        """
        :param int max_position: max length of position
        :return [[None,None],[None,None]...]: generate board as two-dimensional array
        """
        return [[None] * (2 * max_position + 1) for _ in range(2 * max_position + 1)]

    def print_board(self, fields):
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
        self.fields = self.generate_board(self.maxPos)
        self.points = 0
        self.diff = 100
        self.set_castle()

    def set_castle(self):
        """set castle on the middle position of board"""
        self.fields[self.mid][self.mid] = config.CASTLE

    def check_is_correct_move(self, x, y, orientation):
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
        x1, y1 = self.get_second_position_of_puzzle(x, y, orientation)
        if self.is_correct_position(x, y, orientation) and self.is_correct_position(x1, y1):
            x += self.diff
            x1 += self.diff
            y += self.diff
            y1 += self.diff

            if self.is_empty_field(x, y) and self.is_empty_field(x1, y1) and (
                    self.is_near_of_the_puzzle(x, y) or self.is_near_of_the_puzzle(x1, y1)):
                flag = True

        return flag

    def is_empty_field(self, x, y):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :return boolean: return false if field is equal None, otherwise it returns true
        """
        # print(f'[IS EMPTY] Field[{x}][{y}] = {self.fields[x][y]}')
        return self.fields[x][y] is None

    def is_correct_position(self, x, y, orientation=0):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        :return boolean: return true if x, y and orientation have correct value
        """
        allowed_orientation = [0, 90, 180, 270]
        return (self.maxPos >= x >= self.minPos) and (
                self.maxPos >= y >= self.minPos) and orientation in allowed_orientation

    def is_near_of_the_puzzle(self, x, y):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :return boolean: returns true if a puzzle is adjacent to another one
        """
        positions_to_check = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for position in positions_to_check:
            # print(f'[IS NEAR] Field[{posX}][{posY}] = {self.fields[posX][posY]}')
            if self.fields[x + position[0]][y + position[1]] is not None:
                return True
        return False

    def get_second_position_of_puzzle(self, x, y, orientation=0):
        """
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        :return int, int: the coordinates of second position field, which depends on the orientation
        """
        offsets = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}
        offset_x, offset_y = offsets.get(orientation, (0, 0))
        return x + offset_x, y + offset_y

    def add_puzzle_to_the_board(self, puzzle, x, y, orientation):
        """
        Add puzzle to the board, which takes two field
        :param str puzzle: it's key of PUZZLES dictionary
        :param int x: x coordinate of puzzle,
        :param int y: y coordinate of puzzle,
        :param int orientation: orientation of puzzle
        """
        puzzles = PUZZLES[puzzle].split(" ")
        x += 100
        y += 100
        firstPartPuzzle = puzzles[0]
        secondPartPuzzle = puzzles[1]

        self.fields[x][y] = firstPartPuzzle
        x1, y1 = self.get_second_position_of_puzzle(x, y, orientation)
        self.fields[x1][y1] = secondPartPuzzle
        # self.print_board()

    def calculate_result(self):
        """
        :return int: total score of player
        """
        rows = len(self.fields)
        columns = len(self.fields[0])

        for i in range(0, rows):
            for j in range(0, columns):
                field, bonus = self.get_value_and_bonus(self.fields[i][j])
                if bonus is None:
                    bonus = 0
                if field is not None:
                    res, b = self.search_field(field, i, j)
                    bonus += b
                    self.points = self.points + (res + 1) * (bonus + 1)
        return self.points

    def search_field(self, field, i, j):
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
            v, b = self.search_field_recursive(field, i + p[0], j + p[1])
            arr[k] += v
            bonus += b

        return sum(arr), bonus

    def search_field_recursive(self, field, i, j):
        """
        :param str field: kind of the puzzle ex. g - grass, f - forest,
        :param int i: i coordinate of puzzle,
        :param int j: j coordinate of puzzle,
        :return int, int: amount of current adjacent specific type fields, current bonus
        """
        val, b = self.get_value_and_bonus(self.fields[i][j])
        bon = self.get_bonus(b)
        if val == field:
            v, b = self.search_field(field, i, j)
            return v + 1, bon + self.get_bonus(b)
        return 0, 0

    def get_value_and_bonus(self, field):
        """
        :param  str or None field: it's one of part of puzzle example g, m3
        :return str value, int bonus
        :raises Exception for greater length than 2 for field
        """
        if field is None:
            return None, None
        elif len(field) == 1:
            return field[0], None
        elif len(field) == 2:
            return field[0], int(field[1])
        elif len(field) == len(config.CASTLE) and field == config.CASTLE:
            return None, None
        else:
            raise Exception("Incorrect value for field!")

    def get_bonus(self, bonus):
        """
        :param int bonus: value of bonus
        :return int: value of bonus
        """
        return bonus or 0
