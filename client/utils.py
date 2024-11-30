#!/usr/bin/python3
import random
import string
import sys

from common import config


def get_commands():
    username, hacker_mode = None, None
    for arg in sys.argv[1:]:
        config_cmd, _, value = arg.partition("=")
        if config_cmd == config.A_LOGIN:
            username = value
        elif config_cmd == config.A_HACKER_MODE:
            hacker_mode = value
    return username, hacker_mode


def generate_nickname(size):
    return "".join(random.choices(string.ascii_lowercase, k=size))
