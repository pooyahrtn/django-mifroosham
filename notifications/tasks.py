# Create your tasks here
from __future__ import absolute_import, unicode_literals
import requests
from celery import shared_task

BUY = "bu"
SELL = "SE"
DELIVERED = "DE"


@shared_task
def send_notification_sms(**kwargs):
    # if status == BUY:
    #     code = title + ' خریداری شد.'
    #
    if kwargs['status'] == SELL:
        return requests.post(
        'https://api.kavenegar.com/v1/316249736A4D662B556D58676250314B497146656F413D3D/verify/lookup'
        '.json?receptor={0}&token={1}&token2={2}&template=buymifroosham '.format(kwargs['phone_number'],'پست', kwargs['deliver_time']))
    # else:
    #     code = title + 'تحویل داده شد. مبلغ کالا به حساب شما واریز شد.'

    # code = 'kharide'
    # return requests.post(
    #     'https://api.kavenegar.com/v1/316249736A4D662B556D58676250314B497146656F413D3D/verify/lookup'
    #     '.json?receptor={0}&token={1}&template=yadetnareverify '.format(kwargs['phone_number'],kwargs['deliver_time']))
    #


