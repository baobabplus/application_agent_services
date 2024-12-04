class UnauthorizedEmployeeException(Exception):
    def __init__(self, message: str, details: str):
        self.message = message
        self.details = details
        super().__init__(self.message)


class EmployeeNotFoundException(Exception):
    def __init__(self, message: str, details: str):
        self.message = message
        self.details = details
        super().__init__(self.message)
