from django import forms
from django.contrib.auth.models import User

from .models import ChecklistItem, Comment, Project, StatusColumn, Task
from .permissions import user_can_assign_system_users


def _label_user(user: User) -> str:
    full = user.get_full_name().strip()
    if full:
        return f"{full} (@{user.username})"
    return user.username


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "color")
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Nome do projeto"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 3,
                    "placeholder": "O que este projeto entrega?",
                }
            ),
            "color": forms.TextInput(attrs={"class": "input input--color", "type": "color"}),
        }
        labels = {
            "name": "Nome",
            "description": "Descrição",
            "color": "Cor",
        }


class StatusColumnForm(forms.ModelForm):
    class Meta:
        model = StatusColumn
        fields = ("name", "color")
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Nome da coluna"}),
            "color": forms.TextInput(attrs={"class": "input input--color", "type": "color"}),
        }
        labels = {"name": "Nome", "color": "Cor"}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "column",
            "priority",
            "assignee",
            "due_date",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Título da tarefa"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 4,
                    "placeholder": "Detalhes, critérios de aceite…",
                }
            ),
            "column": forms.Select(attrs={"class": "input"}),
            "priority": forms.Select(attrs={"class": "input"}),
            "assignee": forms.Select(attrs={"class": "input"}),
            "due_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
        }
        labels = {
            "title": "Título",
            "description": "Descrição",
            "column": "Status",
            "priority": "Prioridade",
            "assignee": "Responsável",
            "due_date": "Prazo",
        }

    def __init__(self, *args, project=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project or getattr(self.instance, "project", None)
        self.request_user = user
        if not self.project:
            return

        self.fields["column"].queryset = self.project.columns.all()
        self.fields["assignee"].required = False
        self.fields["assignee"].empty_label = "Sem responsável"
        self.fields["assignee"].label_from_instance = _label_user

        can_assign_all = bool(
            self.request_user and user_can_assign_system_users(self.request_user, self.project)
        )
        if can_assign_all:
            self.fields["assignee"].queryset = User.objects.filter(
                is_active=True
            ).order_by("first_name", "username")
            self.fields["assignee"].help_text = (
                "Gerentes e administradores podem atribuir a qualquer usuário do sistema."
            )
        else:
            member_ids = list(self.project.members.values_list("id", flat=True))
            if self.project.owner_id not in member_ids:
                member_ids.append(self.project.owner_id)
            self.fields["assignee"].queryset = User.objects.filter(
                id__in=member_ids, is_active=True
            ).order_by("first_name", "username")
            # Colaborador só vê o campo, mas atribuição limitada aos membros
            if self.request_user and not user_can_assign_system_users(
                self.request_user, self.project
            ):
                # Colaboradores não reatribuem livremente: mantêm apenas leitura via membros
                pass


class QuickTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "assignee")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input input--ghost",
                    "placeholder": "Nova tarefa…",
                    "aria-label": "Título da nova tarefa",
                }
            ),
            "assignee": forms.Select(
                attrs={"class": "input", "aria-label": "Responsável"}
            ),
        }

    def __init__(self, *args, project=None, user=None, include_assignee=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if not include_assignee:
            self.fields.pop("assignee", None)
            return

        self.fields["assignee"].required = False
        self.fields["assignee"].empty_label = "Responsável"
        self.fields["assignee"].label_from_instance = _label_user
        if project and user and user_can_assign_system_users(user, project):
            self.fields["assignee"].queryset = User.objects.filter(
                is_active=True
            ).order_by("first_name", "username")
        elif project:
            member_ids = list(project.members.values_list("id", flat=True))
            if project.owner_id not in member_ids:
                member_ids.append(project.owner_id)
            self.fields["assignee"].queryset = User.objects.filter(
                id__in=member_ids, is_active=True
            ).order_by("first_name", "username")
        else:
            self.fields["assignee"].queryset = User.objects.none()


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ("text",)
        widgets = {
            "text": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Adicionar item…",
                    "aria-label": "Novo item do checklist",
                }
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 3,
                    "placeholder": "Escreva um comentário…",
                    "aria-label": "Comentário",
                }
            ),
        }
        labels = {"body": "Comentário"}
