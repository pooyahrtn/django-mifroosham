"""mifroosham URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from posts import views
# from profiles.views import UserPosts

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^feed/$',views.FeedList.as_view()),
    url(r'^sendpost/$',views.SendPost.as_view()),
    url(r'^userposts/(?P<username>[a-z]+)$',views.UserPosts.as_view()),
    url(r'^likepost/(?P<pk>[0-9]+)$', views.LikePost.as_view())
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)