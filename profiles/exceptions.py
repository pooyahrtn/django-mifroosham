from rest_framework.exceptions import APIException


class FollowException(APIException):
    status_code = 502
    default_detail = 'follow exception'
    default_code = 'follow_exception'


class CreateUserException(APIException):
    status_code = 501
    default_code = 'create_user_error'
    default_detail = 'error while creating error'


