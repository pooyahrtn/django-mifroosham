from collections import OrderedDict

from django.db.models import F
from django.db.models import Q
from django.http import HttpResponse
from django.template import loader
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from profiles.models import Profile, Review, PhoneNumber
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
from .models import QeroonTransaction, qeroon_value
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


# todo: check for disable...
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
            trans.post.disabled = True
            trans.post.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# todo: check for disable...
class CancelSell(APIView):
    serializer_class = CancelSellTransactionSerializer
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
        if serializer.validated_data['disable_post']:
            Post.objects.filter(pk=trans.post.pk).update(disabled=True)
        else:
            Post.objects.filter(pk=trans.post.pk).update(disabled=False)
        Profile.objects.filter(user_id=trans.buyer.pk).update(money=F('money') + trans.suspended_money)
        trans.status = Transaction.CANCELED
        trans.cancel_time = timezone.now()
        trans.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteTransaction(APIView):
    serializer_class = GetTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if trans.post.sender == self.request.user:
            requester_is_sender = True
        elif trans.buyer == self.request.user:
            requester_is_sender = False
        else:
            return Response('not authorized', status=status.HTTP_401_UNAUTHORIZED)
        if trans.status == Transaction.DELIVERED or trans.status == Transaction.CANCELED:

            if requester_is_sender:
                trans.deleted_by_sender = True
            else:
                trans.deleted_by_buyer = True
            trans.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response('transaction can not be deleted cos it is not delivered or canceled')


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
        buyer_profile = get_object_or_404(Profile.objects.select_for_update(), user=self.request.user)
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
            last_transaction.cancel_time = timezone.now()
            last_transaction.auction_failed = True
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
        review = trans.review

        if trans.rate_status == Transaction.RATED:
            if not review:
                raise NotAuthorized('shit happened, transaction has no review')
            Review.objects.change_review(review, for_user=trans.post.sender, rate=serializer.validated_data['rate'],
                                         comment=serializer.validated_data['comment'])
        else:
            if not review:
                trans.review = Review.objects.write_review(for_user=trans.post.sender, reviewer=trans.buyer,
                                                           rate=serializer.validated_data['rate'],
                                                           comment=serializer.validated_data['comment'])
                trans.rate_status = Transaction.RATED
                trans.save()
            else:
                raise NotAuthorized('shit happened, transaction already has review')

        return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionPaginator(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('new_messages', self.new_messages),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class BoughtTransactions(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = BoughtTransactionsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = TransactionPaginator

    def filter_queryset(self, queryset):
        return Transaction.objects.filter(buyer=self.request.user, deleted_by_buyer=False)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        new_messages = queryset.filter(status=Transaction.PENDING).count()
        self.paginator.new_messages = new_messages
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SoldTransactions(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = TransactionPaginator

    def filter_queryset(self, queryset):
        return Transaction.objects.filter(post__sender=self.request.user, deleted_by_sender=False, auction_failed=False)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        new_messages = queryset.filter(status=Transaction.PENDING).count()
        self.paginator.new_messages = new_messages
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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


class InvestHelps(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        template = loader.get_template('helps/invest.json')
        context = {'qeroon_value': qeroon_value, 'your_qeroons': self.request.user.profile.qeroon}
        return HttpResponse(template.render(context, request))


class GetPhoneNumber(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = GetPhoneNumberSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans = serializer.validated_data['transaction']
        if self.request.user == trans.buyer:
            serializer.validated_data['phone_number'] = PhoneNumber.objects.get(user=trans.post.sender).number
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif self.request.user == trans.post.sender:
            serializer.validated_data['phone_number'] = PhoneNumber.objects.get(user=trans.buyer).number
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response('you are bad. not the buyer nor the sender', status=status.HTTP_401_UNAUTHORIZED)
