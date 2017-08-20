import datetime
from django.test import TestCase
from .models import Post, Auction, Discount
from django.utils import timezone
from profiles.models import User
from rest_framework.test import APIRequestFactory
from django.urls import reverse


def create_pooya_and_koorosh(self):
    User.objects.create_user(username='pooya')
    User.objects.create_user(username='koorosh')


class PostModelTest(TestCase):


    def test_post_type_for_auction(self):
        auction = Auction(base_money=0, end_time=timezone.now() + datetime.timedelta(hours=23, minutes=59, seconds=59))
        sender = User.objects.get(username='pooya')
        auction_post = Post(auction=auction, sender=sender, title='fds', price=123, deliver_time=24)
        self.assertIs(auction_post.get_post_type(), 2)


    def test_post_type_for_discount(self):
        discount = Discount(start_price=0, end_time=timezone.now() + datetime.timedelta(hours=24, minutes=0, seconds=0), real_price=2000)
        sender = User.objects.get(username='pooya')
        auction_post = Post(discount=discount, sender=sender, title='fds', price=123, deliver_time=24)
        self.assertIs(auction_post.get_post_type(), 1)

