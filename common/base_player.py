from common import config
from common.utils import encode, decode


class BasePlayer:
    def __init__(self, conn):
        self.conn = conn

    def send_msg(self, msg):
        self.conn.send(encode(msg))

    def recv_msg(self):
        msg = self.conn.recv(config.BUFF_SIZE)
        return decode(msg)

    def get_response(self):
        msg = self.recv_msg()
        msg = msg.replace("\n", '')
        return msg

    def get_command_and_args(self, msg):
        l = msg.strip().replace("\n", "").split(" ")
        if len(l) == 1:
            return l[0], None  # return command
        elif len(l) > 1:
            return l[0], l[1:]  # return command and args