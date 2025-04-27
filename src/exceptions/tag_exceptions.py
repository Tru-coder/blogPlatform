from src.exceptions.exceptions import DefaultNotFoundException, DisplayableException
from fastapi import status

class TagNotFoundException(DefaultNotFoundException):
    pass

class TagAlreadyExistsException(DisplayableException):
    http_status_code = status.HTTP_400_BAD_REQUEST