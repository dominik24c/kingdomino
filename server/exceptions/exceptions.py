__all__ = (
    "CreatingServerFailed",
    "ListeningServerFailed",
    "ConnectionServerFailed",
    "EmptyMessage",
    "NotPassedArgs",
    "TooLongMessage"
)

# Cannot creating server (socket)


class CreatingServerFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


class ListeningServerFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConnectionServerFailed(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmptyMessage(Exception):
    pass


class NotPassedArgs(Exception):
    pass


class TooLongMessage(Exception):
    pass
