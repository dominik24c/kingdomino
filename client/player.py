#!/usr/bin/python3

import random
import sys
import time

from common import config
from common.base_player import BasePlayer

from .dependencies import logger
from .utils import generate_nickname, get_commands


class Player(BasePlayer):
    def __init__(self, conn):
        super().__init__(conn)
        username, hacker_mode = get_commands()
        if username is None:
            username = generate_nickname(10)

        self.name = username
        self.id = 0
        self.in_game = True

        self.player_moves = 0
        self.rounds = 0

        self.pos_x = 0
        self.pos_y = 1
        self.orientation = 0

        self.puzzles = []
        self.puzzle = None

        self.hacker_mode = hacker_mode
        self.receivedMessage = 0
        self.exit_game_after_your_choice = random.randint(2, 10)
        self.flag_timeout_during_game = random.randint(2, 10)

    def login(self, auto_login=True):
        msg = self.get_response()
        if msg == config.S_CONNECT:
            if auto_login:
                command = f"{config.S_LOGIN} {self.name}"
            else:
                nickname = input()
                command = f"{config.S_LOGIN} {nickname}"
            logger.info(f"{config.CLIENT} - {command}")
            self.send_msg(f"{command}")
        else:
            logger.warn(f"{config.SERVER} - Unknown command - {msg}")

    def start_command_handler(self, msg):
        logger.info(f"{config.SERVER} - START")
        _, args = self.get_command_and_args(msg)
        self.id = args[0]
        numberOfPlayers = int(len(args[1:]) / 2)
        self.puzzles = args[1 + numberOfPlayers :]

    def your_choice_command_handler(self):
        logger.info(f"{config.CLIENT} - {config.S_CHOOSE} {self.puzzles[0]}")
        self.send_msg(f"{config.S_CHOOSE} {self.puzzles[0]}")

    def player_choice_command_handler(self, msg):
        logger.info(f"{config.SERVER} - {msg}")
        _, args = self.get_command_and_args(msg)
        self.puzzle = args[2]
        self.puzzles.remove(self.puzzle)

    def round_command_handler(self, msg):
        print(f"{msg}")
        self.puzzles = []
        _, args = self.get_command_and_args(msg)
        if args is None:
            logger.info(f"{config.SERVER} - {config.S_ROUND}")
        else:
            self.puzzles = args
            logger.info(
                f'{config.SERVER} - {config.S_ROUND} {" ".join(self.puzzles)}'
            )

        # print(f'Puzzles {self.puzzles}')

    def your_move_command_handler(self):
        logger.info(f"{config.SERVER} - {config.S_YOUR_MOVE}")
        self.rounds += 1
        if self.rounds == 1:
            pass
        if self.rounds > 1:
            if self.rounds % 2 == 0:
                self.pos_x += 2
            else:
                self.pos_x -= 2
                self.pos_y += 1

        msg = f"{config.S_MOVE} {self.pos_x} {self.pos_y} {self.orientation}"
        self.send_msg(f"{msg}")
        logger.info(f"{config.CLIENT} - {msg}")

    def move_command_handler(self, msg):
        logger.info(f"{config.SERVER} - {msg}")
        _, args = self.get_command_and_args(msg)
        self.player_moves += 1

    def start_game(self):
        while self.in_game:
            message = self.recv_msg()
            # print(messages)
            if message == "":
                self.in_game = False
            else:
                messages = message.split("\n")
                messages = [m for m in messages if m != ""]
                # print(messages)
                for msg in messages:
                    if self.hacker_mode == config.H_EXIT_DURING_GAME:
                        self.exit_during_game()
                    elif self.hacker_mode == config.H_TIMEOUT:
                        self.timeout_during_game()

                    if msg.startswith(config.S_GAME_OVER_RESULTS):
                        response = msg.replace("\n", "")
                        logger.info(f"{config.SERVER} - {response}")
                        self.in_game = False

                    elif msg.startswith(config.S_START):
                        self.start_command_handler(msg)

                    elif msg.startswith(config.S_YOUR_CHOICE):
                        if self.hacker_mode == config.H_EXIT_AFTER_CHOICE:
                            self.exit_after_your_choice()

                        elif self.hacker_mode == config.H_SPAM:
                            self.send_login_messages_infinity()

                        self.your_choice_command_handler()

                    elif msg.startswith(config.S_PLAYER_CHOICE):
                        self.player_choice_command_handler(msg)

                    elif msg.startswith(config.S_ROUND):
                        self.round_command_handler(msg)

                    elif msg.startswith(config.S_YOUR_MOVE):
                        self.your_move_command_handler()

                    elif msg.startswith(config.S_PLAYER_MOVE):
                        self.move_command_handler(msg)

                    elif msg == config.S_OK:
                        logger.info(f"{config.SERVER} - {config.S_OK}")

                    elif msg == config.S_ERROR:
                        logger.info(f"{config.SERVER} - {config.S_ERROR}")

                    else:
                        # print(msg)
                        logger.warn(
                            f"{config.SERVER} - Unknown command: {msg}"
                        )

    def timeout_during_game(self):
        if self.flag_timeout_during_game == self.rounds:
            time.sleep(5)
            sys.exit(1)

    def exit_during_game(self):
        self.receivedMessage += 1
        if self.receivedMessage > config.MAX_RECEIVED_MESSAGE:
            sys.exit(1)

    def exit_after_your_choice(self):
        if self.exit_game_after_your_choice == self.rounds:
            sys.exit(1)

    def send_login_messages_infinity(self):
        while True:
            command = f"{config.S_LOGIN} You have been hacked!"
            self.send_msg(command)
