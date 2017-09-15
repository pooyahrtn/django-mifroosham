from rest_framework.exceptions import APIException


class SendPostException(APIException):
    default_code = 'invalid_post'
    default_detail = 'invalid post'
    status_code = 405


class ShareException(APIException):
    default_detail = 'could not share'
    status_code = 406
    default_code = 'cannot_share'
