from .models import Project


def nav_projects(request):
    if request.user.is_authenticated:
        projects = (
            Project.objects.filter(members=request.user)
            .distinct()
            .order_by("name")[:12]
        )
    else:
        projects = Project.objects.none()
    return {"nav_projects": projects}
