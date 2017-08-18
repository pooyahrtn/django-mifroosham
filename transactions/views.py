from django.db.models import F
from django.db.models import Q
from django.shortcuts import render

from profiles.models import Profile
from .models import Transaction
from rest_framework import generics
from django.db import transaction
from posts.models import Post
from .serializers import TransactionSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import time
from django.utils import timezone
from .exceptions import *


def calculate_discount_current_price(post):
    discount = post.discount
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

    # attention! I do really scare of race condition.

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post.objects.select_for_update(), pk=self.kwargs['post_pk'])
        me = self.request.user
        if post.sender.username == me.username:
            return Response(data='dude you cant do in jib too oon jib', status=status.HTTP_403_FORBIDDEN)
        if post.disabled:
            return Response(data='this post is bought or disabled', status=status.HTTP_403_FORBIDDEN)
        if Transaction.objects.filter(post=post, buyer=self.request.user, status=Transaction.PENDING).exists():
            return Response(data='you bough this shit', status=status.HTTP_302_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        price = 0
        if post.get_post_type() == Post.NORMAL_ITEM:
            price = post.price
            if me.profile.money < price:
                return Response(data='low money', status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                me.profile.money -= price
                me.profile.save()
        elif post.get_post_type() == Post.DISCOUNT_ITEM:
            price = calculate_discount_current_price(post)
            if me.profile.money < price:
                return Response(data='low money', status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                me.profile.money -= price
                me.profile.save()
        # if post.disable_after_buy:
        #     post.disabled = True
        post.save()
        serializer.save(buyer=self.request.user, post=post, suspended_money=price,
                        status=Transaction.PENDING)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CancelBuy(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    # todo! correct with permissions!!!

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

    # permission = transaction.post.

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


class TransactionsList(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
