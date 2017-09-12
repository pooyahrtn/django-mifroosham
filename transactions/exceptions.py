from rest_framework.exceptions import APIException


class SoonForCancelException(APIException):
    status_code = 509
    default_code = 'soon_for_cancel'
    default_detail = 'it is too soon for cancel'


class AlreadyCanceled(APIException):
    status_code = 510
    default_code = 'already_canceled'
    default_detail = 'the post is already canceled'


class AlreadyConfirmed(APIException):
    status_code = 511
    default_code = 'already_confirmed'
    default_detail = 'the post is already confirmed'


class HasNotConfirmed(APIException):
    status_code = 512
    default_code = 'has_not_confirmed'
    default_detail = 'transaction has not confirmed'


class AlreadyDelivered(APIException):
    status_code = 513
    default_detail = 'already_delivered'
    default_code = 'already_delivered'


class YouAreNotAuthorised(APIException):
    status_code = 515
    default_code = 'you_are_not_authorised'
    default_detail = 'you are not authorised'


class MoneyException(APIException):
    status_code = 519
    default_code = 'low_money'
    default_detail = 'you dont have enough money'

class WrongConfirmCode(APIException):
    status_code = 520
    default_code = 'wrong_confirmation_code'
    default_detail = 'wrong confirmation code'

class NotAuthorized(APIException):
    status_code = 521
    default_detail = 'not authorized'
    default_code = 'not_authorized'