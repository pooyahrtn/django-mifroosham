from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^username/(?P<username>[a-z]+)/$', FindUser.as_view(), name='find_user'),
    url(r'^post_title/(?P<title>[^\.,\s]+)/$', FindPostTitle.as_view(), name='find_post_title'),
]
