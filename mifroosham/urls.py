from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from posts import views
from profiles.views import UserDetail

# from profiles.views import UserPosts

urlpatterns = [
    url(r'^$', views.FeedList.as_view()),
    url(r'^admin/', admin.site.urls),
    url(r'^report/', include('reports.urls')),
    url(r'^posts/', include('posts.urls')),
    url(r'^helps/', include('helps.urls')),
    url(r'^profiles/', include('profiles.urls'),name='profiles'),
    url(r'^transactions/', include('transactions.urls')),
    url(r'^notifications/', include('notifications.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^(?P<username>[a-z]+)/$', UserDetail.as_view()),

]
urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)