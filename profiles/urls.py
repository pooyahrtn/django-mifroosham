from django.conf.urls import url

from .views import *


urlpatterns = [
    url(r'^follow/(?P<username>[a-z]+)$', FollowUser.as_view(), name='follow'),
    url(r'^me/', MyProfile.as_view()),
]
