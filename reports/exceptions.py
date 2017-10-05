from rest_framework.exceptions import APIException


class ReportException(APIException):
    status_code = 414

