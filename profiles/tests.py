from django.test import TestCase
from .models import *
from rest_framework.test import APIRequestFactory, APIClient
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import force_authenticate
from .views import *

factory = APIRequestFactory()

def create_pooya_and_koorosh():
    User.objects.create_user(username='pooya')
    User.objects.create_user(username='koorosh')


class FollowTest(APITestCase):
    def test_follow_feed(self):
        create_pooya_and_koorosh()
        token = Token.objects.get(user__username='pooya')
        pooya = User.objects.get(username='pooya')
        koorosh = User.objects.get(username='koorosh')
        self.client.force_authenticate(user=pooya, token=token.key)
        # self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put('/profiles/follow/koorosh')
        self.assertEqual(response.status_code, status.HTTP_200_OK)





