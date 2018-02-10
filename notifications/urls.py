from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^update_notification_token/$', views.MyNotificationToken.as_view()),
    url(r'^transaction_notifications/$', views.TransactionNotifications.as_view()),
    url(r'^read_transaction_notifications/$', views.ReadTransactionNotifications.as_view()),
    url(r'^post_notifications/$', views.PostNotifications.as_view()),
    url(r'^read_post_notifications/$', views.ReadPostNotifications.as_view()),
    url(r'^read_follow_notifications/$', views.ReadFollowNotifications.as_view()),
    url(r'^follow_notifications/$', views.FollowNotifications.as_view()),
]
