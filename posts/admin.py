from django.contrib import admin
from .models import Post, Feed, Auction, Discount


class ConfirmPostFilter(admin.SimpleListFilter):
    title = 'confirmed or what'
    parameter_name = 'confirmation'

    def lookups(self, request, model_admin):
        return (
            ('nconf', 'not confirmed'),
            ('conf', 'confirmed'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'nconf':
            return queryset.filter(confirmed_to_show=False)
        if self.value() == 'conf':
            return queryset.filter(confirmed_to_show=True)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_filter = (ConfirmPostFilter,)
    actions = ['make_published']

    readonly_fields = ('image_tag',)

    def make_published(self, request, queryset):
        rows_updated = queryset.update(confirmed_to_show=True)
        if rows_updated == 1:
            message_bit = "1 story was"
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as published." % message_bit)

    make_published.short_description = "Mark selected stories as published"


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    pass


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    pass


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    pass
