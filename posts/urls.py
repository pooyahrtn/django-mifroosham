from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^like/(?P<uuid>[0-9A-Fa-f-]+)$', views.LikePost.as_view()),
    url(r'^repost/(?P<uuid>[0-9A-Fa-f-]+)$', views.Repost.as_view()),
    url(r'^likers/(?P<pk>[0-9]+)$', views.PostLikers.as_view()),
    url(r'^comments/(?P<uuid>[0-9A-Fa-f-]+)/$', views.Comments.as_view()),
    url(r'^add_comment/$', views.AddComment.as_view()),
    url(r'^delete_comment/$', views.DeleteComment.as_view()),
    url(r'^send/$', views.SendPost.as_view()),
    url(r'^suggest/', views.SuggestPost.as_view()),
    # url(r'^read_feeds/', views.ReadFeeds.as_view()),
    url(r'^users/(?P<username>[a-z]+)/$', views.UserPosts.as_view()),
    url(r'^(?P<uuid>[0-9A-Fa-f-]+)/$', views.PostDetail.as_view()),

]
