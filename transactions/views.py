from django.db.models import F
from django.db.models import Q
from django.shortcuts import render

from profiles.models import Profile
from .models import Transaction
from rest_framework import generics
from django.db import transaction
from posts.models import Post, Auction, Discount
from .serializers import TransactionSerializer, AuctionSuggestSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import time
from django.utils import timezone
from .exceptions import *
from .permissions import *


def calculate_discount_current_price(discount):
    start_time = int(time.mktime(discount.start_time.timetuple()))
    end_time = int(time.mktime(discount.end_time.timetuple()))
    current_time = int(time.time())
    duration = end_time - start_time
    fraction = (current_time - start_time) / duration
    return int(discount.start_price + fraction * (discount.real_price - discount.start_price))


def get_delta_hours(from_date):
    start_time = int(time.mktime(from_date.timetuple()))
    return int((int(time.time()) - start_time) / (24 * 60 * 60))


class BuyPost(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_field = 'post_pk'
    permission_classes = (permissions.IsAuthenticated,)

    # attention! I do really scare of race condition.

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post.objects.select_for_update(), pk=self.kwargs['post_pk'])
        me = self.request.user
        my_profile = get_object_or_404(Profile.objects.select_for_update(), user_id=me.pk)
        if post.sender.username == me.username:
            return Response(data='dude you cant do in jib too oon jib', status=status.HTTP_403_FORBIDDEN)
        if post.disabled:
            return Response(data='this post is bought or disabled', status=status.HTTP_403_FORBIDDEN)
        if Transaction.objects.filter(post=post, buyer=self.request.user, status=Transaction.PENDING).exists():
            return Response(data='you bough this shit', status=status.HTTP_302_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        price = 0
        confirmed = False
        confirm_time = None
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
                confirmed = True
                confirm_time = timezone.now()
                post.disabled = post.disable_after_buy
        post.save()
        serializer.save(buyer=self.request.user, post=post, suspended_money=price,
                        status=Transaction.PENDING, confirmed=confirmed, confirm_time=confirm_time)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CancelBuy(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsBuyerOfTransaction)

    @transaction.atomic
    def perform_update(self, serializer):
        post = self.get_object().post
        trans = self.get_object()
        if trans.buyer.pk != self.request.user.pk:
            raise YouAreNotAuthorised()

        if trans.confirmed:
            if get_delta_hours(trans.confirm_time) < post.deliver_time:
                raise SoonForCancelException()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        self.request.user.profile.money += trans.suspended_money
        Profile.objects.filter(user_id=self.request.user.pk).update(money=F('money') + trans.suspended_money)
        serializer.save(status=Transaction.CANCELED, cancel_time=timezone.now())


class ConfirmSell(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfTransactionsPost)

    @transaction.atomic
    def perform_update(self, serializer):
        trans = self.get_object()
        if trans.post.sender.pk != self.request.user.pk:
            raise YouAreNotAuthorised()

        if trans.confirmed:
            raise AlreadyConfirmed()
        if trans.status == Transaction.CANCELED or trans.status == Transaction.DELIVERED:
            raise AlreadyCanceled()
        if trans.post.disable_after_buy:
            trans.post.disabled = True
            trans.post.save()
            for other_user_transaction in Transaction.objects.filter(Q(post=trans.post), Q(status=Transaction.PENDING),
                                                                     ~Q(pk=trans.pk)):
                Profile.objects.filter(user_id=other_user_transaction.buyer.pk). \
                    update(money=F('money') + other_user_transaction.suspended_money)
        serializer.save(confirmed=True, confirm_time=timezone.now())


class DeliverItem(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsBuyerOfTransaction)

    @transaction.atomic
    def perform_update(self, serializer):
        trans = self.get_object()
        if trans.buyer.pk != self.request.user.pk:
            raise YouAreNotAuthorised()
        if not trans.confirmed:
            raise HasNotConfirmed()
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        seller = trans.post.sender
        Profile.objects.filter(user_id=seller.pk).update(money=F('money') + trans.suspended_money)
        serializer.save(status=Transaction.DELIVERED, deliver_time=timezone.now())


class CancelSell(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOfTransactionsPost)

    @transaction.atomic
    def perform_update(self, serializer):
        trans = self.get_object()
        if trans.post.sender.pk != self.request.user.pk:
            raise YouAreNotAuthorised()
        if trans.status == Transaction.DELIVERED:
            raise AlreadyDelivered()
        if trans.status == Transaction.CANCELED:
            raise AlreadyCanceled()
        if not trans.confirmed:
            raise AlreadyConfirmed()
        buyer = trans.buyer
        Profile.objects.filter(user_id=buyer.pk).update(money=F('money') + trans.suspended_money)
        serializer.save(status=Transaction.CANCELED, cancel_time=timezone.now())


class AuctionSuggestHigher(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = AuctionSuggestSerializer
    permission_classes = (permissions.IsAuthenticated, IsNotOwnerOfPost)

    @transaction.atomic
    def perform_create(self, serializer):
        buyer = self.request.user
        buyer_profile = get_object_or_404(Profile.objects.select_for_update(), pk=buyer.pk)
        post = get_object_or_404(Post.objects.select_for_update(), pk=self.kwargs['pk'])
        trans = serializer.save()
        auction = get_object_or_404(Auction.objects.select_for_update(), pk=post.auction_id)

        if trans.suspended_money > buyer_profile.money:
            raise MoneyException()

        # people who attempted buy this post but they have lower suggest.(normally it should be one person)
        this_post_buyers = Transaction.objects.filter(post=post, status=Transaction.PENDING).order_by('-suspended_money')

        if this_post_buyers.count() > 0:
            min_price = this_post_buyers[0].suspended_money + 1
        else:
            min_price = auction.base_money

        if trans.suspended_money < min_price:
            raise MoneyException()

        trans.buyer = buyer
        trans.post = post
        auction.highest_suggest = trans.suspended_money
        buyer_profile.money -= trans.suspended_money
        for last_transaction in this_post_buyers:
            his_suspended_money = last_transaction.suspended_money
            last_transaction.status = Transaction.CANCELED
            Profile.objects.filter(user_id=last_transaction.buyer.pk).update(money=F('money') + his_suspended_money)
            last_transaction.save()
        buyer_profile.save()
        auction.save()
        trans.confirmed = True
        trans.confirm_time = timezone.now()
        trans.save()


class TransactionsList(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
