from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^post/', views.ReportPostView.as_view()),
]