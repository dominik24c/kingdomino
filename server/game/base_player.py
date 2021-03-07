#!/usr/bin/python3
from config import *


class BasePlayer(object):
    def __init__(self, conn, code, buffSize, idPlayer):
        self.conn = conn
        self.code = code
        self.buffSize = buffSize
        self.isConnection = True
        self.idPlayer = idPlayer

    def sendMsg(self, msg):
        try:
            self.conn.send(msg.encode(self.code))
        except Exception:
            m = msg.replace('\n', '')
            self.logger.error(
                f'{CLIENT} Connection lost! {self.idPlayer}, cannot send: {m}')
            self.isConnection = False

    def recvMsg(self):
        msg = self.conn.recv(self.buffSize)
        return msg.decode(self.code)
