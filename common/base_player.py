from common import config
from common.utils import decode, encode


class BasePlayer:
    def __init__(self, conn):
        self.conn = conn

    def send_msg(self, msg):
        self.conn.send(encode(msg))

    def recv_msg(self):
        return decode(self.conn.recv(config.BUFF_SIZE))

    def get_response(self):
        return self.recv_msg().replace("\n", "")

    def get_command_and_args(self, msg):
        messages = msg.strip().replace("\n", "").split(" ")
        return messages[0], (messages[1:] if len(messages) > 1 else None)
