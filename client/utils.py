#!/usr/bin/python3
import sys
import random

from common import config

def get_commands():
    username = None
    hacker_mode = None
    if len(sys.argv) > 1:
        min_index = 1
        for i in range(min_index, len(sys.argv)):
            result = sys.argv[i].split("=")
            if len(result) == 2:
                if result[0] == config.A_LOGIN:
                    username = result[1]
                elif result[0] == config.A_HACKER_MODE:
                    hacker_mode = result[1]
    return username, hacker_mode

def generate_nickname(size):
    start = ord("a")
    end = ord("z")
    nickname = ""
    for _ in range(size):
        decimal_ascii_sign = random.randint(start, end)
        nickname += chr(decimal_ascii_sign)

    return nickname
