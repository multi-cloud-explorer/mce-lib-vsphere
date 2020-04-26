__all__ = [
    "FatalError",
    "ConnectionError",
    "VmNotFoundError",
    "NotPoweredError",
    "NotValidToolsError",
    "AuthenticationError",
]

class FatalError(Exception):
    pass


class ConnectionError(Exception):
    pass


class VmNotFoundError(FatalError):
    pass


class NotPoweredError(FatalError):
    pass


class NotValidToolsError(FatalError):
    pass


class AuthenticationError(FatalError):
    pass

