from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^investment/$', Investment.as_view()),
    url(r'^send_post_helps/$', SendPostHelps.as_view()),

]
