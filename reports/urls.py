from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^post/', views.ReportPostView.as_view()),
    url(r'^comment/', views.ReportComment.as_view()),
]