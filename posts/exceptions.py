from rest_framework.exceptions import APIException


class SendPostException(APIException):
    default_code = 'invalid_post'
    default_detail = 'invalid post'
    status_code = 542
