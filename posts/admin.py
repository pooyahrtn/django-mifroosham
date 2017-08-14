from django.contrib import admin
from .models import Post , Feed, Auction, Discount


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    pass

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    pass

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    pass
