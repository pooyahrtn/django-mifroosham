from . import serializers
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from django.template import loader


class Investment(APIView):
    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/investment.md')
        context = {}
        return HttpResponse(template.render(context, request))


class SendPostHelps(APIView):

    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/send_post_helps.json')
        context = {}
        return HttpResponse(template.render(context, request))


class BuyPostHelps(APIView):

    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/buy_post_helps.json')
        context = {}
        return HttpResponse(template.render(context, request))


class TransactionHelps(APIView):

    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/transaction_helps.json')
        context = {}
        return HttpResponse(template.render(context, request))



