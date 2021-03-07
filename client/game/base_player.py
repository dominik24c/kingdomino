#!/usr/bin/python3

class BasePlayer(object):
    def __init__(self, conn, codeSystem, buffSize):
        self.conn = conn
        self.codeSystem = codeSystem
        self.buffSize = buffSize

    def sendMsg(self, msg):
        self.conn.send(msg.encode(self.codeSystem))

    def recvMsg(self):
        msg = self.conn.recv(self.buffSize)
        return msg.decode(self.codeSystem)
