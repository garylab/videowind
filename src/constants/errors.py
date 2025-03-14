class InputError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ServerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class LoginError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UnAuthError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFound(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

