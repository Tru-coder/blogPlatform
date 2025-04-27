from fastapi import status


class AppException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DisplayableException(AppException):
    http_status_code = status.HTTP_418_IM_A_TEAPOT

    def __init__(self, message: str):
        super().__init__(message)

class DefaultNotFoundException(DisplayableException):
    http_status_code = status.HTTP_404_NOT_FOUND