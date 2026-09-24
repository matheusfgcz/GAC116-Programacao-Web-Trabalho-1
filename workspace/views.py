import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    ChecklistItemForm,
    CommentForm,
    ProjectForm,
    QuickTaskForm,
    StatusColumnForm,
    TaskForm,
)
from .models import ChecklistItem, Project, StatusColumn, Task
from .permissions import (
    user_can_access_project,
    user_can_assign_system_users,
    user_can_create_project,
    user_can_manage_project,
)


def safe_next_url(request, fallback: str) -> str:
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return fallback


def task_detail_url(task_id: int, next_url: str | None = None) -> str:
    url = reverse("workspace:task_detail", kwargs={"pk": task_id})
    if next_url:
        from urllib.parse import urlencode

        return f"{url}?{urlencode({'next': next_url})}"
    return url


def accessible_tasks(user):
    from .permissions import get_profile

    profile = get_profile(user)
    if profile and profile.is_admin:
        return Task.objects.all()
    return Task.objects.filter(
        Q(project__owner=user) | Q(project__members=user)
    ).distinct()


def accessible_projects(user):
    from .permissions import get_profile

    profile = get_profile(user)
    if profile and profile.is_admin:
        return Project.objects.all()
    return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()


class ProjectAccessMixin(LoginRequiredMixin):
    project_url_kwarg = "pk"

    def get_project(self) -> Project:
        project = get_object_or_404(Project, pk=self.kwargs[self.project_url_kwarg])
        if not user_can_access_project(self.request.user, project):
            raise Http404
        return project


def ensure_assignee_is_member(project: Project, assignee) -> None:
    """Se a tarefa for atribuída a alguém de fora, inclui como membro do projeto."""
    if assignee is None:
        return
    project.add_member(assignee, role="member")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "workspace/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        projects = accessible_projects(user).annotate(
            task_count=Count("tasks", distinct=True)
        )
        # Tabela do dashboard: tarefas "A Fazer" atribuídas ao usuário logado
        todo_tasks = (
            Task.objects.filter(
                assignee=user,
                column__name__iexact="A Fazer",
            )
            .select_related("project", "column")
            .order_by("due_date", "-updated_at")
        )
        overdue = Task.objects.filter(
            assignee=user,
            due_date__lt=timezone.localdate(),
        ).exclude(column__name__iexact="Concluído")
        ctx.update(
            {
                "projects": projects,
                "project_count": projects.count(),
                "my_tasks": todo_tasks,
                "my_task_count": todo_tasks.count(),
                "overdue_count": overdue.count(),
                "overdue_tasks": overdue.select_related("project", "column")[:5],
                "can_create_project": user_can_create_project(user),
            }
        )
        return ctx


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "workspace/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return accessible_projects(self.request.user).annotate(
            task_count=Count("tasks", distinct=True)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ProjectForm()
        from .permissions import user_can_create_project as can_create

        ctx["can_create_project"] = can_create(self.request.user)
        return ctx


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "workspace/project_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not user_can_create_project(request.user):
            messages.error(
                request,
                "Apenas Gerentes ou Administradores podem criar projetos.",
            )
            return redirect("workspace:project_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.add_member(self.request.user, role="owner")
        self.object.seed_default_columns()
        messages.success(self.request, "Projeto criado com sucesso.")
        return response

    def get_success_url(self):
        return reverse("workspace:project_board", kwargs={"pk": self.object.pk})


class ProjectUpdateView(ProjectAccessMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "workspace/project_settings.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not user_can_manage_project(request.user, self.object):
            messages.error(request, "Você não tem permissão para configurar este projeto.")
            return redirect("workspace:project_board", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return accessible_projects(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object
        ctx["column_form"] = StatusColumnForm()
        ctx["columns"] = self.object.columns.all()
        ctx["can_manage"] = True
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Projeto atualizado.")
        return reverse("workspace:project_settings", kwargs={"pk": self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "workspace/project_confirm_delete.html"
    success_url = reverse_lazy("workspace:project_list")

    def get_queryset(self):
        return accessible_projects(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not user_can_manage_project(request.user, self.object):
            messages.error(request, "Apenas o dono/gerente pode excluir o projeto.")
            return redirect("workspace:project_board", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Projeto excluído.")
        return super().form_valid(form)


class ProjectBoardView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = "workspace/project_board.html"
    context_object_name = "project"

    def get_queryset(self):
        return accessible_projects(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        columns = (
            self.object.columns.prefetch_related("tasks__assignee")
            .all()
        )
        ctx["columns"] = columns
        ctx["quick_form"] = QuickTaskForm(
            project=self.object,
            user=self.request.user,
            include_assignee=user_can_assign_system_users(
                self.request.user, self.object
            ),
        )
        ctx["column_form"] = StatusColumnForm(initial={"color": "#94A3B8"})
        ctx["view_mode"] = "board"
        ctx["can_manage"] = user_can_manage_project(self.request.user, self.object)
        ctx["can_create_project"] = user_can_create_project(self.request.user)
        ctx["can_assign"] = user_can_assign_system_users(
            self.request.user, self.object
        )
        return ctx


class ProjectListModeView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = "workspace/project_list_view.html"
    context_object_name = "project"

    def get_queryset(self):
        return accessible_projects(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related("column", "assignee")
        priority = self.request.GET.get("priority")
        status = self.request.GET.get("status")
        if priority:
            tasks = tasks.filter(priority=priority)
        if status:
            tasks = tasks.filter(column_id=status)
        ctx["tasks"] = tasks
        ctx["columns"] = self.object.columns.all()
        ctx["selected_priority"] = priority or ""
        ctx["selected_status"] = status or ""
        ctx["priorities"] = Task.Priority.choices
        ctx["view_mode"] = "list"
        ctx["can_manage"] = user_can_manage_project(self.request.user, self.object)
        return ctx


@login_required
@require_POST
def quick_create_task(request, pk, column_id):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_access_project(request.user, project):
        return HttpResponseForbidden()
    column = get_object_or_404(StatusColumn, pk=column_id, project=project)
    can_assign = user_can_assign_system_users(request.user, project)
    form = QuickTaskForm(
        request.POST,
        project=project,
        user=request.user,
        include_assignee=can_assign,
    )
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.column = column
        task.created_by = request.user
        max_pos = column.tasks.order_by("-position").values_list("position", flat=True).first()
        task.position = (max_pos or 0) + 1
        if not can_assign:
            task.assignee = None
        task.save()
        if can_assign and task.assignee_id:
            ensure_assignee_is_member(project, task.assignee)
        messages.success(request, "Tarefa adicionada.")
    else:
        messages.error(request, "Não foi possível criar a tarefa.")
    return redirect("workspace:project_board", pk=project.pk)


@login_required
@require_POST
def create_column(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_manage_project(request.user, project):
        return HttpResponseForbidden()
    form = StatusColumnForm(request.POST)
    if form.is_valid():
        column = form.save(commit=False)
        column.project = project
        max_order = project.columns.order_by("-order").values_list("order", flat=True).first()
        column.order = (max_order or 0) + 1
        column.save()
        messages.success(request, "Coluna criada.")
    else:
        messages.error(request, "Não foi possível criar a coluna. Verifique o nome.")
    next_url = request.POST.get("next") or reverse("workspace:project_board", kwargs={"pk": pk})
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("workspace:project_board", pk=project.pk)


@login_required
@require_POST
def update_column(request, pk, column_id):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_manage_project(request.user, project):
        return HttpResponseForbidden()
    column = get_object_or_404(StatusColumn, pk=column_id, project=project)
    form = StatusColumnForm(request.POST, instance=column)
    if form.is_valid():
        form.save()
        messages.success(request, "Coluna atualizada.")
    else:
        messages.error(request, "Não foi possível atualizar a coluna.")
    next_url = request.POST.get("next") or reverse("workspace:project_board", kwargs={"pk": pk})
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("workspace:project_board", pk=project.pk)


@login_required
@require_POST
def delete_column(request, pk, column_id):
    project = get_object_or_404(Project, pk=pk)
    if not user_can_manage_project(request.user, project):
        return HttpResponseForbidden()
    column = get_object_or_404(StatusColumn, pk=column_id, project=project)
    if project.columns.count() <= 1:
        messages.error(request, "O projeto precisa de pelo menos uma coluna.")
    elif column.tasks.exists():
        messages.error(request, "Mova as tarefas antes de excluir a coluna.")
    else:
        column.delete()
        messages.success(request, "Coluna removida.")
    next_url = request.POST.get("next") or reverse("workspace:project_board", kwargs={"pk": pk})
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("workspace:project_board", pk=project.pk)


class TaskCreateView(ProjectAccessMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "workspace/task_form.html"
    project_url_kwarg = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        ctx["can_assign"] = user_can_assign_system_users(
            self.request.user, self.project
        )
        return ctx

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        max_pos = (
            form.instance.column.tasks.order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        form.instance.position = (max_pos or 0) + 1
        response = super().form_valid(form)
        ensure_assignee_is_member(self.project, self.object.assignee)
        messages.success(self.request, "Tarefa criada.")
        return response

    def get_success_url(self):
        return reverse("workspace:task_detail", kwargs={"pk": self.object.pk})


class TaskDetailView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "workspace/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return accessible_tasks(self.request.user).select_related(
            "project", "column", "assignee"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.object.project
        kwargs["user"] = self.request.user
        return kwargs

    def get_back_url(self) -> str:
        fallback = reverse(
            "workspace:project_board", kwargs={"pk": self.object.project_id}
        )
        return safe_next_url(self.request, fallback)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        back_url = self.get_back_url()
        ctx["project"] = self.object.project
        ctx["checklist_form"] = ChecklistItemForm()
        ctx["comment_form"] = CommentForm()
        ctx["checklist"] = self.object.checklist_items.all()
        ctx["comments"] = self.object.comments.select_related("author")
        ctx["back_url"] = back_url
        ctx["next_url"] = back_url
        ctx["can_assign"] = user_can_assign_system_users(
            self.request.user, self.object.project
        )
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        ensure_assignee_is_member(self.object.project, self.object.assignee)
        messages.success(self.request, "Tarefa atualizada.")
        return response

    def get_success_url(self):
        if self.request.POST.get("close") == "1":
            return self.get_back_url()
        return task_detail_url(self.object.pk, self.get_back_url())


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "workspace/task_confirm_delete.html"

    def get_queryset(self):
        return Task.objects.filter(
            Q(project__owner=self.request.user) | Q(project__members=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fallback = reverse(
            "workspace:project_board", kwargs={"pk": self.object.project_id}
        )
        ctx["back_url"] = safe_next_url(self.request, fallback)
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Tarefa excluída.")
        fallback = reverse(
            "workspace:project_board", kwargs={"pk": self.object.project_id}
        )
        return safe_next_url(self.request, fallback)


def _redirect_task_detail(request, task):
    fallback = reverse("workspace:project_board", kwargs={"pk": task.project_id})
    next_url = safe_next_url(request, fallback)
    return redirect(task_detail_url(task.pk, next_url))


@login_required
@require_POST
def add_checklist_item(request, pk):
    task = get_object_or_404(accessible_tasks(request.user), pk=pk)
    form = ChecklistItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.task = task
        max_order = task.checklist_items.order_by("-order").values_list("order", flat=True).first()
        item.order = (max_order or 0) + 1
        item.save()
    return _redirect_task_detail(request, task)


@login_required
@require_POST
def toggle_checklist_item(request, pk, item_id):
    task = get_object_or_404(accessible_tasks(request.user), pk=pk)
    item = get_object_or_404(ChecklistItem, pk=item_id, task=task)
    item.done = not item.done
    item.save(update_fields=["done"])
    return _redirect_task_detail(request, task)


@login_required
@require_POST
def delete_checklist_item(request, pk, item_id):
    task = get_object_or_404(accessible_tasks(request.user), pk=pk)
    item = get_object_or_404(ChecklistItem, pk=item_id, task=task)
    item.delete()
    return _redirect_task_detail(request, task)


@login_required
@require_POST
def add_comment(request, pk):
    task = get_object_or_404(accessible_tasks(request.user), pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        messages.success(request, "Comentário publicado.")
    return _redirect_task_detail(request, task)


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "workspace/search.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = (self.request.GET.get("q") or "").strip()
        projects = accessible_projects(self.request.user)
        tasks = accessible_tasks(self.request.user).select_related("project", "column")
        if query:
            projects = projects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            tasks = tasks.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        else:
            projects = projects.none()
            tasks = tasks.none()
        ctx.update(
            {
                "query": query,
                "projects": projects.annotate(task_count=Count("tasks", distinct=True))[:20],
                "tasks": tasks[:30],
            }
        )
        return ctx


class TaskReorderView(LoginRequiredMixin, View):
    """JSON endpoint for Kanban drag-and-drop."""

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

        task_id = payload.get("task_id")
        column_id = payload.get("column_id")
        ordered_ids = payload.get("ordered_ids") or []

        task = get_object_or_404(Task, pk=task_id)
        if not user_can_access_project(request.user, task.project):
            return JsonResponse({"ok": False, "error": "Sem permissão"}, status=403)

        column = get_object_or_404(StatusColumn, pk=column_id, project=task.project)
        task.column = column
        task.save(update_fields=["column", "updated_at"])

        for index, tid in enumerate(ordered_ids):
            Task.objects.filter(pk=tid, project=task.project).update(position=index)

        return JsonResponse({"ok": True})
