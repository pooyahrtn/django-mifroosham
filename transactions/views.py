from django.db.models import F
from django.db.models import Q
from rest_framework.views import APIView
from profiles.models import Profile
from .models import Transaction
from rest_framework import generics
from django.db import transaction
from posts.models import Post, Auction, Discount
from .serializers import TransactionSerializer, BuyTransactionSerializer, \
    GetTransactionSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import time
from django.utils import timezone
from .exceptions import *
from .permissions import *
import datetime
from notifications.models import TransactionNotification


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
        if post.disabled:
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
                                           status=Transaction.PENDING, reposter=reposter)
        TransactionNotification.objects.create_notification(transaction=trans, user=me,
                                                            status=TransactionNotification.BUY)
        TransactionNotification.objects.create_notification(transaction=trans, user=post.sender,
                                                            status=TransactionNotification.SELL)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelBuy(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsBuyerOfTransaction)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.buyer.pk != self.request.user.pk:
            raise YouAreNotAuthorised()
        now = timezone.now()
        if now - trans.time < datetime.timedelta(hours=trans.post.deliver_time):
            raise SoonForCancelException()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        self.request.user.profile.money += trans.suspended_money
        Profile.objects.filter(user_id=self.request.user.pk).update(money=F('money') + trans.suspended_money)
        trans.cancel_time = timezone.now()
        trans.save()
        return Response(serializer.data, status.HTTP_200_OK)


# class ConfirmSell(generics.UpdateAPIView):
#     queryset = Transaction.objects.all()
#     serializer_class = TransactionSerializer
#     permission_classes = (permissions.IsAuthenticated, IsOwnerOfTransactionsPost)
#     lookup_field = 'uuid'
#
#     @transaction.atomic
#     def perform_update(self, serializer):
#         trans = self.get_object()
#         if trans.post.sender.pk != self.request.user.pk:
#             raise YouAreNotAuthorised()
#         if trans.confirmed:
#             raise AlreadyConfirmed()
#         if trans.status == Transaction.CANCELED or trans.status == Transaction.DELIVERED:
#             raise AlreadyCanceled()
#         if trans.post.disable_after_buy:
#             trans.post.disabled = True
#             trans.post.save()
#             for other_user_transaction in Transaction.objects.filter(Q(post=trans.post), Q(status=Transaction.PENDING),
#                                                                      ~Q(pk=trans.pk)):
#                 Profile.objects.filter(user_id=other_user_transaction.buyer.pk). \
#                     update(money=F('money') + other_user_transaction.suspended_money)
#         serializer.save(confirmed=True, confirm_time=timezone.now())
#

class DeliverItem(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsBuyerOfTransaction)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.buyer.pk != self.request.user.pk:
            raise YouAreNotAuthorised()
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        seller = trans.post.sender
        reposter = trans.reposter
        if reposter:
            Profile.objects.filter(user_id=reposter.pk).update(money=F('money') + trans.suspended_money * 0.05)
            Profile.objects.filter(user__username='pooya').update(money=F('money') + trans.suspended_money * 0.05)
        else:
            Profile.objects.filter(user__username='pooya').update(money=F('money') + trans.suspended_money * 0.1)
        Profile.objects.filter(user_id=seller.pk).update(money=F('money') + trans.suspended_money * 0.9)
        trans.status = Transaction.DELIVERED
        trans.deliver_time = timezone.now()
        trans.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelSell(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfTransactionsPost)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.post.sender.pk != self.request.user.pk:
            raise YouAreNotAuthorised()
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
            # if not trans.confirmed:
            #     raise AlreadyConfirmed()
        buyer = trans.buyer
        Profile.objects.filter(user_id=buyer.pk).update(money=F('money') + trans.suspended_money)
        trans.status = Transaction.CANCELED
        trans.cancel_time = timezone.now()
        trans.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuctionSuggestHigher(APIView):
    serializer_class = BuyTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsNotOwnerOfPost)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.validated_data['post']
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
            raise MoneyException()

        auction.highest_suggest = higher_suggest
        buyer_profile.money -= higher_suggest
        for last_transaction in this_post_buyers:
            his_suspended_money = last_transaction.suspended_money
            last_transaction.status = Transaction.CANCELED
            Profile.objects.filter(user_id=last_transaction.buyer.pk).update(money=F('money') + his_suspended_money)
            last_transaction.save()
        buyer_profile.save()
        auction.save()
        Transaction.objects.create(buyer=self.request.user, post=post, reposter=reposter)
        return Response(serializer.data, status=status.HTTP_200_OK)



class MyTransactions(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def filter_queryset(self, queryset):
        return Transaction.objects.filter(Q(buyer=self.request.user) | Q(post__sender=self.request.user))
