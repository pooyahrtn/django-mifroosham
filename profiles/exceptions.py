from rest_framework.exceptions import APIException


class FollowException(APIException):
    status_code = 700
    default_detail = 'follow exception'
    default_code = 'follow_exception'