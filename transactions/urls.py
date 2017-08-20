from django.conf.urls import url

from .views import *


urlpatterns = [
    url(r'^cancel/(?P<pk>[0-9]+)$', CancelBuy.as_view()),
    url(r'^buy/(?P<post_pk>[0-9]+)$', BuyPost.as_view()),
    url(r'^confirm_sell/(?P<pk>[0-9]+)$', ConfirmSell.as_view()),
    url(r'^deliver/(?P<pk>[0-9]+)$', DeliverItem.as_view()),
    url(r'^auction_suggest_higher/(?P<pk>[0-9]+)$', AuctionSuggestHigher.as_view()),
    url(r'^cancel_sell/(?P<pk>[0-9]+)$', CancelSell.as_view()),
]
