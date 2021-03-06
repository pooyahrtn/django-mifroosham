from django.conf.urls import url

from .views import *
from rest_framework.authtoken import views


urlpatterns = [
    url(r'^follow/(?P<username>[a-z]+)$', FollowUser.as_view(), name='follow'),
    url(r'^user_reviews/(?P<username>[a-z]+)/$', UserReviews.as_view(), name='user_review'),
    url(r'^user_followers/(?P<username>[a-z]+)/$', UserFollowers.as_view(), name='user_followers'),
    url(r'^user_followings/(?P<username>[a-z]+)/$', UserFollowings.as_view(), name='user_followings'),
    url(r'^me/$', MyProfile.as_view()),
    url(r'^update_photo/$', UpdateProfilePhoto.as_view()),
    url(r'^sign_up/$', SignUp.as_view()),
    url(r'^login/$', Login.as_view()),
    url(r'^request_confirmation/$', RequestConfirmation.as_view(), name='request_login'),
    # url(r'^api-token-auth/', views.obtain_auth_token)
]
