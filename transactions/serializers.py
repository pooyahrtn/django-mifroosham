from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from posts.serializers import PostSerializer
from .models import Transaction
from profiles.serializers import UserSerializer
from posts.models import Feed, Post
from django.contrib.auth.models import User


class BuyTransactionSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(label="post_uuid")
    reposter_username = serializers.CharField(label='reposter_username')

    def validate(self, attrs):
        post_uuid = attrs.get('post_uuid')
        reposter_username = attrs.get('reposter_username')
        post = get_object_or_404(Post,uuid=post_uuid)
        reposter = None
        if User.objects.filter(username=reposter_username).exists():
            reposter = User.objects.get(username=reposter_username)
        attrs['post'] = post
        attrs['reposter'] = reposter
        return attrs


class GetTransactionSerializer(serializers.Serializer):
    transaction_uuid = serializers.UUIDField()

    def validate(self, attrs):
        transaction_uuid = attrs.get('transaction_uuid')
        transaction = get_object_or_404(Transaction, uuid=transaction_uuid)
        attrs['transaction'] = transaction
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    buyer = UserSerializer(read_only=True)
    suspended_money = serializers.ReadOnlyField()
    confirmed = serializers.BooleanField(read_only=True)
    confirm_time = serializers.ReadOnlyField()
    deliver_time = serializers.ReadOnlyField()
    cancel_time = serializers.ReadOnlyField()
    reposter = UserSerializer(read_only=True)

    class Meta:
        model = Transaction
        exclude = ('id',)


class AuctionSuggestSerializer(BuyTransactionSerializer):
    higher_suggest = serializers.IntegerField()
    #
    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     higher_suggest = attrs.get()