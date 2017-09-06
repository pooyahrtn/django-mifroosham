import re
from django.contrib import admin

from posts.utils import value_of_feed
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

    def save_model(self, request, obj, form, change):
        if obj.confirmed_to_show and obj.waiting_to_confirm:
            obj.waiting_to_confirm = False
            pattern = re.compile("#([^\s]+)")
            m = pattern.findall(obj.description)
            from tags.models import Tag
            for tag in m:
                Tag.objects.get_or_create(name=tag, post=obj)
            obj.save()
            value = value_of_feed(obj.sender.profile.score, obj.sender.profile.count_of_rates, 1)
            for user in obj.sender.follow.followers.all():
                Feed.objects.create(user=user, post=obj, not_read_sort_value=value)
            Feed.objects.create(user=obj.sender, post=obj, not_read_sort_value=2147483647, buyable=False)
        super(PostAdmin, self).save_model(request, obj, form, change)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    pass


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    pass


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    pass
