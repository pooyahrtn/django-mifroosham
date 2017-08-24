# Create your tasks here
from __future__ import absolute_import, unicode_literals
import requests
from celery import shared_task


@shared_task
def send_sms(phone_number, code):
    return requests.post(
        'https://api.kavenegar.com/v1/316249736A4D662B556D58676250314B497146656F413D3D/verify/lookup'
        '.json?receptor={0}&token={1}&template=yadetnareverify '.format(phone_number, code))

