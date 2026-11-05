from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descrição", blank=True)
    color = models.CharField("Cor", max_length=7, default="#00B4A6")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Dono",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="projects",
        blank=True,
        verbose_name="Membros",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self) -> str:
        return f"{self.name} ({self.owner})"

    def seed_default_columns(self) -> None:
        defaults = [
            ("A Fazer", 0, "#94A3B8"),
            ("Em Progresso", 1, "#38BDF8"),
            ("Concluído", 2, "#34D399"),
        ]
        for name, order, color in defaults:
            StatusColumn.objects.get_or_create(
                project=self,
                name=name,
                defaults={"order": order, "color": color},
            )

    def add_member(self, user, role: str = "member") -> "ProjectMembership":
        membership, _ = ProjectMembership.objects.update_or_create(
            project=self,
            user=user,
            defaults={"role": role},
        )
        self.members.add(user)
        return membership

    def user_role(self, user) -> str | None:
        if user.is_superuser:
            return ProjectMembership.Role.OWNER
        if self.owner_id == user.id:
            return ProjectMembership.Role.OWNER
        membership = self.memberships.filter(user=user).first()
        if membership:
            return membership.role
        if self.members.filter(id=user.id).exists():
            return ProjectMembership.Role.MEMBER
        return None

    def user_can_manage(self, user) -> bool:
        role = self.user_role(user)
        return role in {
            ProjectMembership.Role.OWNER,
            ProjectMembership.Role.MANAGER,
        }


class ProjectMembership(models.Model):
    """Papel do usuário dentro de um projeto (permissões distintas)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Dono"
        MANAGER = "manager", "Gerente"
        MEMBER = "member", "Membro"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Projeto",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        verbose_name="Usuário",
    )
    role = models.CharField(
        "Papel no projeto",
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField("Entrou em", auto_now_add=True)

    class Meta:
        verbose_name = "Participação no projeto"
        verbose_name_plural = "Participações no projeto"
        unique_together = ("project", "user")
        ordering = ["project", "role", "user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} · {self.project.name} ({self.get_role_display()})"


class StatusColumn(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="columns",
        verbose_name="Projeto",
    )
    name = models.CharField("Nome", max_length=80)
    order = models.PositiveIntegerField("Ordem", default=0)
    color = models.CharField("Cor", max_length=7, default="#94A3B8")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Coluna"
        verbose_name_plural = "Colunas"

    def __str__(self) -> str:
        return f"{self.project.name} · {self.name}"


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Projeto",
    )
    column = models.ForeignKey(
        StatusColumn,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Coluna / Status",
    )
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição", blank=True)
    priority = models.CharField(
        "Prioridade",
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Responsável",
    )
    due_date = models.DateField("Prazo", null=True, blank=True)
    position = models.PositiveIntegerField("Posição", default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"

    def __str__(self) -> str:
        return f"{self.title} - {self.project.name} - {self.get_priority_display()}"

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        if self.column.name.lower() in {"concluído", "concluido", "done"}:
            return False
        return self.due_date < timezone.localdate()


class ChecklistItem(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="checklist_items",
        verbose_name="Tarefa",
    )
    text = models.CharField("Texto", max_length=255)
    done = models.BooleanField("Concluído", default=False)
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Item de checklist"
        verbose_name_plural = "Itens de checklist"

    def __str__(self) -> str:
        status = "OK" if self.done else "Pendente"
        return f"{self.text} ({status})"


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Tarefa",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
        verbose_name="Autor",
    )
    body = models.TextField("Comentário")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"

    def __str__(self) -> str:
        return f"Comentário de {self.author} em {self.task.title}"
