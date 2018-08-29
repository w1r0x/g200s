class AuthenticationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.errors = {'message': 'Authentication required'}


class SetModeError(Exception):
    def __init__(self, data):
        message = 'Can\'t set mode. Are you stop previous operation?'
        super().__init__(message)
        self.errors = {'message': message, 'data': data}


class RunError(Exception):
    def __init__(self, data):
        message = 'Can\'t run current mode. Are you stop previous operation?'
        super().__init__(message)
        self.errors = {'message': message, 'data': data}


class StopError(Exception):
    def __init__(self, data):
        message = 'Can\'t stop. May be no operation run?'
        super().__init__(message)
        self.errors = {'message': message, 'data': data}
