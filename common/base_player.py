from common import config
from common.utils import encode, decode


class BasePlayer:
    def __init__(self, conn):
        self.conn = conn

    def sendMsg(self, msg):
        self.conn.send(encode(msg))

    def recvMsg(self):
        msg = self.conn.recv(config.BUFF_SIZE)
        return decode(msg)
