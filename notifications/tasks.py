# Create your tasks here
from __future__ import absolute_import, unicode_literals
import requests
from celery import shared_task
import json

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
            '.json?receptor={0}&token={1}&token2={2}&template=buymifroosham '.format(kwargs['phone_number'], 'پست',
                                                                                     kwargs['deliver_time']))
        # else:
        #     code = title + 'تحویل داده شد. مبلغ کالا به حساب شما واریز شد.'

        # code = 'kharide'
        # return requests.post(
        #     'https://api.kavenegar.com/v1/316249736A4D662B556D58676250314B497146656F413D3D/verify/lookup'
        #     '.json?receptor={0}&token={1}&template=yadetnareverify '.format(kwargs['phone_number'],kwargs['deliver_time']))
        #


@shared_task
def send_push_notification(**kwargs):
    url = 'https://onesignal.com/api/v1/notifications'
    headers = {'Content-type': 'application/json'}
    if kwargs['status'] == SELL:
        text = kwargs['title'] + ' فروخته شد.'
    elif kwargs['status'] == DELIVERED:
        text = kwargs['title'] + 'تحویل داده شد.'
    else:
        return
    body = {
        "include_player_ids": [str(kwargs['id']), ],
        "app_id": "d55c41b1-3107-44f5-a9b6-49acbd1cb07f",
        "contents": {"en": text},
        "data": {"status": kwargs['status'], "transaction_uuid": kwargs['transaction_uuid']}
    }
    return requests.post(url, json.dumps(body), headers=headers)
