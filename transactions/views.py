from django.shortcuts import render
from .models import Transaction
from rest_framework import generics
from django.db import transaction
from posts.models import Post
from .serializers import TransactionSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import time


def calculate_discount_current_price(post):
    discount = post.discount
    start_time = int(time.mktime(discount.start_time.timetuple()))
    end_time = int(time.mktime(discount.end_time.timetuple()))
    current_time = int(time.time())
    duration = end_time - start_time
    fraction = (current_time-start_time)/duration
    return int(discount.start_price + fraction * (discount.real_price - discount.start_price))


class BuyPost(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_field = 'post_pk'
    # attention! I do really scare of race condition.
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post.objects.select_for_update(), pk=self.kwargs['post_pk'])
        me = self.request.user
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
        if post.disable_after_buy:
            post.disabled = True

        post.save()
        serializer.save(buyer=self.request.user, post=post, suspended_money=price,
                        status=Transaction.PENDING)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # @transaction.atomic
    # def perform_create(self, serializer):
    #     post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
    #


class TransactionsList(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer