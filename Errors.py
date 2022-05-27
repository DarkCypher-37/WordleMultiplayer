class NetworkError(Exception):
    pass

class ConnectionClosedError(NetworkError):
    def __str__(self) -> str:
        return "Remote has closed the connection"

class MagicNumberMisMatchError(NetworkError):
    def __str__(self) -> str:
        return "magic number doesnt match"

class MessageTooBigError(NetworkError):
    def __str__(self) -> str:
        return "message_string part of a message was larger than 2**12 = 4096 bytes"

class ConnectExError(NetworkError):
    def __init__(self, errno) -> None:
        self.errno = errno

    def __str__(self) -> str:
        return f"during a connect_ex() attempt an error occured (errno: {self.errno})"

class CouldNotCreateNetworkError(Exception):
    pass

class CouldNotJoinError(Exception):
    pass

class CharTooLongError(ValueError):
    pass

class WordTooLongError(ValueError):
    pass