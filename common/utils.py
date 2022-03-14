from . import config


def encode(message):
    return f'{message}\n'.encode(config.UTF8)


def decode(message):
    return message.decode(config.UTF8)
