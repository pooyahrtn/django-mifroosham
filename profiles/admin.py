from django.contrib import admin

from .models import User, Follow, PhoneNumberConfirmation, PhoneNumber, Review



@admin.register(User)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('image_tag',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass


@admin.register(PhoneNumberConfirmation)
class PhoneConfirmation(admin.ModelAdmin):
    pass

admin.site.register(PhoneNumber)
admin.site.register(Review)


