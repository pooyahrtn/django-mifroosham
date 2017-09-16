from rest_framework import serializers


class SendPostSerializer(serializers.Serializer):
    investment = serializers.CharField()
    charity = serializers.CharField()
    deliver_time = serializers.CharField()
    discount = serializers.CharField()
    auction = serializers.CharField()
