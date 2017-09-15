from django.conf.urls import url

from .views import *


urlpatterns = [
    url(r'^cancel$', CancelBuy.as_view()),
    url(r'^buy$', BuyPost.as_view()),
    url(r'^invest$', InvestOnPost.as_view()),
    url(r'^write_review$', WriteReview.as_view()),
    # url(r'^confirm_sell/(?P<uuid>[0-9A-Fa-f-]+)$', ConfirmSell.as_view()),
    url(r'^deliver$', DeliverItem.as_view()),
    url(r'^auction_suggest_higher', AuctionSuggestHigher.as_view()),
    url(r'^cancel_sell$', CancelSell.as_view()),
    url(r'^bought$', BoughtTransactions.as_view()),
    url(r'^sold', SoldTransactions.as_view()),
    url(r'^invests', MyInvests.as_view()),
    url(r'^return_invest', ReturnInvest.as_view())
]
