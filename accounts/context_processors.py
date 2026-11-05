from .models import UserProfile


def user_profile(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": UserProfile.Role.ADMIN
                if request.user.is_superuser
                else UserProfile.Role.MEMBER
            },
        )
    return {"user_profile": profile}
