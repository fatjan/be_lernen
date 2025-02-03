from rest_framework.exceptions import APIException
from rest_framework import status

class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict: The resource already exists."
    default_code = "conflict"

