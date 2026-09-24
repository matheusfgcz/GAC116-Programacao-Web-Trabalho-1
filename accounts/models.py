from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Perfil global do usuário com papéis distintos de permissão."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MANAGER = "manager", "Gerente"
        MEMBER = "member", "Colaborador"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Usuário",
    )
    role = models.CharField(
        "Perfil",
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    bio = models.CharField("Bio", max_length=255, blank=True)

    class Meta:
        verbose_name = "Perfil de usuário"
        verbose_name_plural = "Perfis de usuário"

    def __str__(self) -> str:
        return f"{self.user.username} — {self.get_role_display()}"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.user.is_superuser

    @property
    def is_manager(self) -> bool:
        return self.is_admin or self.role == self.Role.MANAGER

    @property
    def can_create_projects(self) -> bool:
        return self.is_manager


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        role = UserProfile.Role.ADMIN if instance.is_superuser else UserProfile.Role.MEMBER
        UserProfile.objects.create(user=instance, role=role)
    else:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                "role": UserProfile.Role.ADMIN
                if instance.is_superuser
                else UserProfile.Role.MEMBER
            },
        )
