from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_profile_role",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "profile__role", "groups")
    search_fields = ("username", "first_name", "last_name", "email")

    @admin.display(description="Perfil", ordering="profile__role")
    def get_profile_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_role_display() if profile else "—"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "bio")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "bio")
    list_editable = ("role",)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
