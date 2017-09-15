from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from posts.serializers import PostSerializer
from .models import Transaction, QeroonTransaction
from profiles.serializers import UserSerializer, ReviewSerializer
from posts.models import Feed, Post
from django.contrib.auth.models import User


class BuyTransactionSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(label="post_uuid")
    reposter_username = serializers.CharField(label='reposter_username')

    def validate(self, attrs):
        post_uuid = attrs.get('post_uuid')
        reposter_username = attrs.get('reposter_username')
        post = get_object_or_404(Post, uuid=post_uuid)
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


class DeliverTransactionSerializer(GetTransactionSerializer):
    confirm_code = serializers.IntegerField()


class WriteReviewSerializer(GetTransactionSerializer):
    rate = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=400, allow_null=True, allow_blank=True)


class InvestOnPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(label="post_uuid")
    value = serializers.IntegerField()


transaction_base_fields = ('post', 'status', 'buyer', 'suspended_money', 'deliver_time', 'cancel_time',
                           'reposter', 'uuid', 'review')


class TransactionSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    buyer = UserSerializer(read_only=True)
    suspended_money = serializers.ReadOnlyField()
    deliver_time = serializers.ReadOnlyField()
    cancel_time = serializers.ReadOnlyField()
    reposter = UserSerializer(read_only=True)
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = transaction_base_fields


class BoughtTransactionsSerializer(TransactionSerializer):
    confirm_code = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = transaction_base_fields + ('confirm_code',)


class AuctionSuggestSerializer(BuyTransactionSerializer):
    higher_suggest = serializers.IntegerField()
    #
    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     higher_suggest = attrs.get()


class QeroonTransactionsSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    suspended_qeroon = serializers.ReadOnlyField()
    requested_time = serializers.ReadOnlyField()
    got_time = serializers.ReadOnlyField()
    cancel_time = serializers.ReadOnlyField()
    post = PostSerializer(read_only=True)
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = QeroonTransaction
        fields = ('status', 'suspended_qeroon', 'requested_time', 'got_time', 'cancel_time', 'post', 'uuid')


class ReturnInvestSerializer(serializers.Serializer):
    transaction_uuid = serializers.UUIDField()
    qeroons = serializers.IntegerField(read_only=True)