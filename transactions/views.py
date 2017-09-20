from django.db.models import F
from django.db.models import Q
from rest_framework.views import APIView
from profiles.models import Profile, Review
from rest_framework import generics
from django.db import transaction
from posts.models import Auction, Discount
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import time
from django.utils import timezone
from .exceptions import *
from .permissions import *
import datetime
from notifications.models import TransactionNotification
from .models import QeroonTransaction
import random


def calculate_discount_current_price(discount):
    start_time = int(time.mktime(discount.start_time.timetuple()))
    end_time = int(time.mktime(discount.end_time.timetuple()))
    current_time = int(time.time())
    duration = end_time - start_time
    fraction = (current_time - start_time) / duration
    return int(discount.start_price + fraction * (discount.real_price - discount.start_price))


class BuyPost(APIView):
    serializer_class = BuyTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.validated_data['post']
        reposter = serializer.validated_data['reposter']
        me = self.request.user
        my_profile = get_object_or_404(Profile.objects.select_for_update(), user_id=me.pk)
        if post.sender.username == me.username:
            return Response(data='dude you cant do in jib too oon jib', status=status.HTTP_403_FORBIDDEN)
        if post.disabled or not post.confirmed_to_show:
            return Response(data='this post is bought or disabled', status=status.HTTP_403_FORBIDDEN)
        if Transaction.objects.filter(post=post, buyer=self.request.user, status=Transaction.PENDING).exists():
            return Response(data='you bough this shit', status=status.HTTP_302_FOUND)

        if post.get_post_type() == Post.NORMAL_ITEM:
            price = post.price
            if my_profile.money < price:
                return Response(data='low money', status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                my_profile.money -= price
                my_profile.save()
        elif post.get_post_type() == Post.DISCOUNT_ITEM:
            discount = get_object_or_404(Discount, pk=post.discount.pk)
            price = calculate_discount_current_price(discount)
            if my_profile.money < price:
                return Response(data='low money', status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                my_profile.money -= price
                my_profile.save()
        else:
            return Response(data='not allowed', status=status.HTTP_405_METHOD_NOT_ALLOWED)
        post.disabled = post.disable_after_buy
        post.save()
        trans = Transaction.objects.create(buyer=self.request.user, post=post, suspended_money=price,
                                           status=Transaction.PENDING, reposter=reposter,
                                           confirm_code=random.randint(100000, 999999))
        TransactionNotification.objects.create_notification(transaction=trans, user=me,
                                                            status=TransactionNotification.BUY)
        TransactionNotification.objects.create_notification(transaction=trans, user=post.sender,
                                                            status=TransactionNotification.SELL)
        data = serializer.data
        data['confirm_code'] = trans.confirm_code
        return Response(data, status=status.HTTP_201_CREATED)


class InvestOnPost(APIView):
    serializer_class = InvestOnPostSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post_uuid = serializer.validated_data['post_uuid']
        value = serializer.validated_data['value']
        post = get_object_or_404(Post.objects.select_for_update(), uuid=post_uuid)
        if post.disabled or not post.confirmed_to_show:
            return Response(data='this post is bought or disabled', status=status.HTTP_403_FORBIDDEN)

        user_qeroons = self.request.user.profile.qeroon
        if user_qeroons < value:
            return Response('not enough qeroons to perform', status=status.HTTP_400_BAD_REQUEST)
        if post.remaining_qeroons < value:
            return Response('post qeroons are less than requested value', status.HTTP_410_GONE)
        if value < 1:
            return Response('value should more than 1', status=status.HTTP_400_BAD_REQUEST)
        self.request.user.profile.qeroon = F('qeroon') - value
        self.request.user.profile.save()
        post.remaining_qeroons = F('remaining_qeroons') - value
        post.total_invested_qeroons = F('total_invested_qeroons') + value
        post.save()
        QeroonTransaction.objects.create(suspended_qeroon=value, status=QeroonTransaction.REQUESTED, post=post,
                                         user=self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelBuy(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        now = timezone.now()
        if trans.buyer != self.request.user:
            raise NotAuthorized()
        if trans.post.get_post_type == 2:
            if now - trans.post.auction.end_time < datetime.timedelta(days=trans.post.deliver_time):
                raise SoonForCancelException()
        elif now - trans.time < datetime.timedelta(days=trans.post.deliver_time):
            raise SoonForCancelException()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        self.request.user.profile.money += trans.suspended_money
        Profile.objects.filter(user=trans.buyer).update(money=F('money') + trans.suspended_money)
        trans.cancel_time = timezone.now()
        trans.rate_status = Transaction.CAN_RATE
        trans.save()
        return Response(serializer.data, status.HTTP_200_OK)


class DeliverItem(APIView):
    serializer_class = DeliverTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.post.sender != self.request.user:
            raise NotAuthorized()
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        if serializer.validated_data['confirm_code'] != trans.confirm_code:
            raise WrongConfirmCode()

        reposter = trans.reposter
        if reposter:
            Profile.objects.filter(user_id=reposter.pk).update(total_successful_reposts=
                                                               F('total_successful_reposts') + 1)
        if trans.post.ads_included:
            Profile.objects.filter(user=trans.post.sender).update(money=F('money') + trans.suspended_money * 0.9)
            Profile.objects.filter(user=trans.buyer).update(qeroon=F('qeroon') + trans.post.total_invested_qeroons)
        else:
            Profile.objects.filter(user=trans.post.sender).update(money=F('money') + trans.suspended_money)
        trans.status = Transaction.DELIVERED
        trans.deliver_time = timezone.now()
        trans.rate_status = Transaction.CAN_RATE
        trans.save()
        QeroonTransaction.objects.give_investors_money(post=trans.post)
        if trans.post.get_post_type == 2:
            trans.post.disabled = trans.post.disable_after_buy
            trans.post.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelSell(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.post.sender != self.request.user:
            return Response('not authorized', status=status.HTTP_401_UNAUTHORIZED)
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
            # if not trans.confirmed:
            #     raise AlreadyConfirmed()
        Profile.objects.filter(user_id=trans.buyer.pk).update(money=F('money') + trans.suspended_money)
        trans.status = Transaction.CANCELED
        trans.cancel_time = timezone.now()
        trans.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuctionSuggestHigher(APIView):
    serializer_class = AuctionSuggestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.validated_data['post']
        if self.request.user == post.sender:
            return Response('bad request', status=status.HTTP_401_UNAUTHORIZED)
        if post.disabled or not post.confirmed_to_show:
            return Response(data='this post is bought or disabled', status=status.HTTP_403_FORBIDDEN)
        higher_suggest = serializer.validated_data['higher_suggest']
        reposter = serializer.validated_data['reposter']
        buyer_profile = get_object_or_404(Profile.objects.select_for_update(), pk=self.request.user.pk)
        auction = get_object_or_404(Auction.objects.select_for_update(), pk=post.auction_id)
        if higher_suggest > buyer_profile.money:
            raise MoneyException()

            # people who attempted buy this post but they have lower suggest.(normally it should be one person)
        this_post_buyers = Transaction.objects.filter(post=post, status=Transaction.PENDING).order_by(
            '-suspended_money')

        if this_post_buyers.count() > 0:
            min_price = this_post_buyers[0].suspended_money + 1
        else:
            min_price = auction.base_money

        if higher_suggest < min_price:
            return Response(data='your suggest is less than the highest', status=413)

        auction.highest_suggest = higher_suggest
        buyer_profile.money = F('money') - higher_suggest
        for last_transaction in this_post_buyers:
            his_suspended_money = last_transaction.suspended_money
            last_transaction.status = Transaction.CANCELED
            Profile.objects.filter(user_id=last_transaction.buyer.pk).update(money=F('money') + his_suspended_money)
            last_transaction.save()

        buyer_profile.save()
        auction.save()
        trans = Transaction.objects.create(buyer=self.request.user, post=post, reposter=reposter,
                                           suspended_money=higher_suggest, confirm_code=random.randint(100000, 999999))
        data = serializer.data
        data['confirm_code'] = trans.confirm_code
        return Response(data, status=status.HTTP_201_CREATED)


class WriteReview(APIView):
    serializer_class = WriteReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if self.request.user != trans.buyer:
            raise NotAuthorized()
        if trans.rate_status == Transaction.NOT_RATEABLE:
            raise NotAuthorized('you can not rate this transaction')
        if trans.rate_status == Transaction.RATED:
            raise NotAuthorized('you already rated this post')
        review = trans.review
        if not review:
            trans.review = Review.objects.write_review(for_user=trans.post.sender, reviewer=trans.buyer,
                                                       rate=serializer.validated_data['rate'],
                                                       comment=serializer.validated_data['comment'])
            trans.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class BoughtTransactions(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = BoughtTransactionsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset):
        return Transaction.objects.filter(buyer=self.request.user)


class SoldTransactions(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset):
        return Transaction.objects.filter(post__sender=self.request.user)


class MyInvests(generics.ListAPIView):
    queryset = QeroonTransaction.objects.all()
    serializer_class = QeroonTransactionsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset):
        return QeroonTransaction.objects.filter(user=self.request.user)


class ReturnInvest(APIView):
    serializer_class = ReturnInvestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        q_transaction = get_object_or_404(QeroonTransaction, uuid=serializer.validated_data['transaction_uuid'])
        if q_transaction.user != self.request.user:
            raise NotAuthorized()
        Profile.objects.filter(user=q_transaction.user).update(qeroon=F('qeroon') + q_transaction.suspended_qeroon)
        q_transaction.post.total_invested_qeroons = F('total_invested_qeroons') - q_transaction.suspended_qeroon
        q_transaction.post.remaining_qeroons = F('remaining_qeroons') + q_transaction.suspended_qeroon
        q_transaction.post.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
