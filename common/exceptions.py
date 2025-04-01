class BadRequestException(Exception):
    pass


class CustomException(Exception):

    def __init__(self, error_details):
        self.error_details = error_details


class ValidationFailedException(CustomException):
    error_message = "VALIDATION_FAILED"

    def __init__(self, error_details):
        super().__init__(error_details)


class RequiredDataNotFound(CustomException):
    def __init__(self, error_details):
        super().__init__(error_details)


class TransactionNotFound(Exception):
    pass
