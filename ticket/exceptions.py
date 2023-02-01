from rest_framework.exceptions import APIException


class Unauthorized(APIException):
    status_code = 403
    default_code = 'ERR_UNAUTHORIZED'


class Unavailable(APIException):
    status_code = 500
    default_detail = 'Try again later.'
    default_code = 'ERR_UNAVAILABLE'
