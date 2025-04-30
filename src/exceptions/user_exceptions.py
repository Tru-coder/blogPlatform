from src.exceptions.exceptions import DefaultNotFoundException, DisplayableException, AppException
from fastapi import status

class UserNotFoundException(DefaultNotFoundException):
    pass

class UserAlreadyExistsException(DisplayableException):
    http_status_code = status.HTTP_400_BAD_REQUEST

class UserPasswordIsMissingException(AppException):
    pass