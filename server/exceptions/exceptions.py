class GameException(Exception):
    """Main Game Exception"""


class ServerException(Exception):
    """Main Server Exception"""


class CommandReaderException(Exception):
    """Main Command Reader Exception"""


class CreatingServerFailed(ServerException):
    pass


class ListeningServerFailed(ServerException):
    pass


class ConnectionServerFailed(ServerException):
    pass


class EmptyMessage(CommandReaderException):
    pass


class NotPassedArgs(CommandReaderException):
    pass


class TooLongMessage(CommandReaderException):
    pass
