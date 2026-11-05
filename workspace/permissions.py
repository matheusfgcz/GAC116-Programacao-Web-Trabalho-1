from accounts.models import UserProfile

from .models import Project


def get_profile(user) -> UserProfile | None:
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": UserProfile.Role.ADMIN
            if user.is_superuser
            else UserProfile.Role.MEMBER
        },
    )
    return profile


def user_can_create_project(user) -> bool:
    profile = get_profile(user)
    return bool(profile and profile.can_create_projects)


def user_can_access_project(user, project: Project) -> bool:
    if not user.is_authenticated:
        return False
    profile = get_profile(user)
    if profile and profile.is_admin:
        return True
    return project.user_role(user) is not None


def user_can_manage_project(user, project: Project) -> bool:
    """Admin, dono/gerente do projeto, ou Gerente global participante."""
    if not user.is_authenticated:
        return False
    profile = get_profile(user)
    if profile and profile.is_admin:
        return True
    if project.user_can_manage(user):
        return True
    # Gerente global pode gerenciar projetos dos quais faz parte
    if profile and profile.role == UserProfile.Role.MANAGER:
        return project.user_role(user) is not None
    return False


def user_can_assign_system_users(user, project: Project) -> bool:
    """Gerente/Admin podem atribuir tarefas a qualquer usuário do sistema."""
    return user_can_manage_project(user, project)
