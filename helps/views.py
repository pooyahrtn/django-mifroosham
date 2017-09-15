from django.shortcuts import render
from rest_framework import status
from django.http import HttpResponse
from rest_framework.views import APIView
from django.template import loader


class Investment(APIView):
    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/investment.md')
        context = {}
        return HttpResponse(template.render(context, request))
