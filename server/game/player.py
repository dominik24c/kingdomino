import threading

from common import config
from common.base_player import BasePlayer

from ..dependencies import logger
from ..utils import get_command_and_args_from_player
from .board import Board


class Player(BasePlayer, threading.Thread):
    def __init__(self, conn, game, unique_id, name=""):
        super().__init__(conn)
        threading.Thread.__init__(self)

        self.name = name
        self.game = game
        self.in_game = True
        self.puzzle = None
        self.is_connection = True
        self.your_turn = threading.Event()
        self.your_turn.set()
        self.board = Board()
        self.is_login = True
        self.unique_id = unique_id
        self.errors_count = 0

    def send_msg(self, msg):
        try:
            super().send_msg(msg)
        except Exception:
            m = msg.replace("\n", "")
            logger.error(
                f"{config.CLIENT} Connection lost! \
                    {self.unique_id}, cannot send: {m}"
            )
            self.is_connection = False

    def get_player_info(self):
        return f"[PLAYER {self.unique_id}] - "

    def send_error(self):
        self.errors_count += 1
        self.send_msg(f"{config.S_ERROR}")
        logger.error(
            f"{config.CLIENT} {self.get_player_info()} {config.S_ERROR}"
        )

    def message_handler(self):
        return [m for m in self.recv_msg().split("\n") if m]

    def login(self, args):
        if len(args) == 1 and not self.name:
            self.name = args[0]
            logger.info(
                f"{config.CLIENT} {self.get_player_info()} \
                    Set nickname: {self.name}"
            )
            self.send_msg(f"{config.S_OK}")
            self.errors_count = 0
        else:
            logger.error(
                f"{config.CLIENT} {self.get_player_info()} Cannot set nickname!"
            )
            logger.error(
                f"{config.CLIENT} {self.get_player_info()} Your args: {args}"
            )
            self.send_error()

    def move(self, args):
        try:
            if len(args) != 3:
                raise Exception
            x, y, orientation = int(args[0]), int(args[1]), int(args[2])
            if self.game.legalMove(self, x=x, y=y, orientation=orientation):
                self.errors_count = 0
                logger.info(
                    f"{config.CLIENT} {self.get_player_info()}\
                          {config.S_MOVE}: {self.unique_id}"
                )
            else:
                self.send_error()
        except Exception:
            self.send_error()

    def choose_move(self, args):
        try:
            if len(args) != 1:
                raise Exception
            puzzle = int(args[0])
            if self.game.legalMove(self, puzzle):
                logger.info(
                    f"{config.CLIENT} {self.get_player_info()}\
                          {config.S_CHOOSE}: {puzzle}"
                )
                self.errors_count = 0
            else:
                self.send_error()
        except Exception:
            self.send_error()

    def get_timeout(self):
        if self.is_login:
            self.is_login = False
        return config.TIMEOUT_LOGIN if self.is_login else config.TIMEOUT

    def run(self):
        messages = None
        while self.is_connection and self.in_game:
            if self.your_turn.is_set():
                # print('waiting for response')
                timeout = self.get_timeout()
                try:
                    logger.info(
                        f"{config.CLIENT} {self.get_player_info()}"
                        "waiting for response"
                    )
                    self.conn.settimeout(timeout)
                    messages = self.message_handler()
                    self.conn.settimeout(None)
                except IndexError:
                    self.send_error()
                except TypeError:
                    logger.error(
                        f"{config.CLIENT} {self.get_player_info()}"
                        " lost connection"
                    )
                    self.is_connection = False
                except TimeoutError:
                    logger.error(
                        f"{config.CLIENT} {self.get_player_info()} timeout!"
                    )
                    self.is_connection = False
                except Exception as e:
                    print(f"{type(e).__name__} exception")
                    logger.error(f"{config.CLIENT} {self.get_player_info()} {e}")
                    self.conn.close()

                if messages is not None and len(messages) > 0:
                    for m in messages:
                        if len(m) >= config.MAX_LENGTH_OF_MSG:
                            logger.error(
                                f"{config.CLIENT} {self.get_player_info()} "
                                f"Too Long message! Client {self.unique_id}"
                                " was kicked!"
                            )
                            self.is_connection = False

                        command, args = get_command_and_args_from_player(m)
                        logger.info(
                            f"{config.CLIENT} {self.get_player_info()}\
                                  {command} {args}"
                        )

                        if self.is_connection:
                            if command in config.ALLOWED_CLIENT_COMMANDS:
                                if command == config.S_LOGIN:
                                    self.login(args)
                                    while self.game.wait_for_players.is_set():
                                        pass
                                elif command == config.S_CHOOSE:
                                    self.choose_move(args)
                                elif command == config.S_MOVE:
                                    self.move(args)
                                else:
                                    logger.warn(
                                        f"{config.CLIENT} "
                                        f"{self.get_player_info()}"
                                        "Unknown command"
                                    )
                                    self.send_error()
                            else:
                                logger.warn(
                                    f"{config.CLIENT} {self.get_player_info()} "
                                    "Not allowed command"
                                )
                                self.send_error()

                        if self.errors_count >= config.NUM_OF_ERRORS:
                            logger.error(
                                f"{config.CLIENT} {self.get_player_info()} \
                                    Too much errors from client. "
                                f"Client {self.unique_id} was kicked!"
                            )
                            self.is_connection = False
                            break

                elif messages is not None and len(messages) == 0:
                    logger.error(
                        f"{config.CLIENT} {self.get_player_info()}"
                        " lost connection!"
                    )
                    self.is_connection = False
