from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from workspace.models import ChecklistItem, Comment, Project, ProjectMembership, Task


class Command(BaseCommand):
    help = "Cria usuários, perfis e um projeto FlowTask de exemplo."

    def handle(self, *args, **options):
        admin_user = self._ensure_user(
            username="admin",
            password="admin",
            first_name="Admin",
            email="admin@flowtask.local",
            is_staff=True,
            is_superuser=True,
            role=UserProfile.Role.ADMIN,
        )
        manager = self._ensure_user(
            username="gerente",
            password="gerente234",
            first_name="Ana",
            email="gerente@flowtask.local",
            role=UserProfile.Role.MANAGER,
        )
        member = self._ensure_user(
            username="membro",
            password="membro1234",
            first_name="Bruno",
            email="membro@flowtask.local",
            role=UserProfile.Role.MEMBER,
        )

        project, project_created = Project.objects.get_or_create(
            name="Lançamento FlowTask",
            owner=manager,
            defaults={
                "description": "Workspace de demonstração.",
                "color": "#00B4A6",
            },
        )
        project.add_member(manager, role=ProjectMembership.Role.OWNER)
        project.add_member(member, role=ProjectMembership.Role.MEMBER)
        project.add_member(admin_user, role=ProjectMembership.Role.MANAGER)

        if project_created or not project.columns.exists():
            project.seed_default_columns()
            self.stdout.write(self.style.SUCCESS("Projeto demo pronto."))
        else:
            self.stdout.write("Projeto demo já existe.")

        columns = {c.name: c for c in project.columns.all()}
        if project.tasks.exists():
            self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
            self._print_credentials()
            return

        today = timezone.localdate()
        samples = [
            {
                "title": "Definir escopo do MVP",
                "column": "Concluído",
                "priority": Task.Priority.HIGH,
                "due_date": today - timedelta(days=3),
                "description": "Mapear board, lista e detalhe de tarefa.",
                "assignee": manager,
            },
            {
                "title": "Montar design system",
                "column": "Em Progresso",
                "priority": Task.Priority.URGENT,
                "due_date": today + timedelta(days=1),
                "description": "Tokens de cor, tipografia Sora + IBM Plex Sans.",
                "assignee": manager,
            },
            {
                "title": "Implementar drag-and-drop",
                "column": "Em Progresso",
                "priority": Task.Priority.HIGH,
                "due_date": today + timedelta(days=2),
                "description": "Reordenar cards entre colunas via API JSON.",
                "assignee": member,
            },
            {
                "title": "Tela de dashboard",
                "column": "A Fazer",
                "priority": Task.Priority.MEDIUM,
                "due_date": today + timedelta(days=5),
                "description": "Resumo de projetos, tarefas e atrasos.",
                "assignee": member,
            },
            {
                "title": "Checklist de acessibilidade",
                "column": "A Fazer",
                "priority": Task.Priority.LOW,
                "due_date": today - timedelta(days=1),
                "description": "Labels, foco visível e skip link.",
                "assignee": member,
            },
        ]

        for index, sample in enumerate(samples):
            column = columns.get(sample["column"]) or project.columns.first()
            task = Task.objects.create(
                project=project,
                column=column,
                title=sample["title"],
                description=sample["description"],
                priority=sample["priority"],
                assignee=sample["assignee"],
                due_date=sample["due_date"],
                position=index,
                created_by=manager,
            )
            ChecklistItem.objects.create(
                task=task, text="Revisar critérios de aceite", order=0
            )
            ChecklistItem.objects.create(
                task=task, text="Validar no mobile", order=1, done=index == 0
            )
            Comment.objects.create(
                task=task,
                author=manager,
                body="Comentário de demonstração para a arguição do trabalho.",
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self._print_credentials()

    def _ensure_user(
        self,
        *,
        username,
        password,
        first_name,
        email,
        role,
        is_staff=False,
        is_superuser=False,
    ):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuário {username} criado."))
        else:
            changed = False
            if is_staff and not user.is_staff:
                user.is_staff = True
                changed = True
            if is_superuser and not user.is_superuser:
                user.is_superuser = True
                changed = True
            if changed:
                user.save()
            self.stdout.write(f"Usuário {username} já existe.")

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=["role"])
        return user

    def _print_credentials(self):
        self.stdout.write("Admin:   admin / admin  -> /admin/")
        self.stdout.write("Gerente: gerente / gerente1234")
        self.stdout.write("Membro:  membro / membro1234")
