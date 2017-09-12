from django.contrib import admin

from .models import Profile, Follow, PhoneNumberConfirmation, PhoneNumber, Review


# class ProfileInline(admin.StackedInline):
#     model = Profile
#     can_delete = False
#     verbose_name_plural = 'Profile'
#     fk_name = 'user'
#
#
# class CustomUserAdmin(UserAdmin):
#     inlines = (ProfileInline, )
#
#     def get_inline_instances(self, request, obj=None):
#         if not obj:
#             return list()
#         return super(CustomUserAdmin, self).get_inline_instances(request, obj)
#
#
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)

@admin.register(Profile)
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


