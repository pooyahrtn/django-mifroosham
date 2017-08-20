from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^like/(?P<pk>[0-9]+)$', views.LikePost.as_view()),
    url(r'^repost/(?P<pk>[0-9]+)$', views.Repost.as_view()),
    url(r'^likers/(?P<pk>[0-9]+)$', views.PostLikers.as_view()),
    url(r'^comments/(?P<pk>[0-9]+)$', views.Comments.as_view()),
    url(r'^send/$', views.SendPost.as_view()),
    url(r'^suggest/', views.SuggestPost.as_view()),
    url(r'^(?P<pk>[0-9]+)$', views.PostDetail.as_view()),
]
