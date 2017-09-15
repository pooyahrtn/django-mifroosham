from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^investment/$', Investment.as_view(), name='follow'),

]
