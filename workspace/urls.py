from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "workspace"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="workspace:dashboard"),
        name="home",
    ),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/", views.ProjectBoardView.as_view(), name="project_board"),
    path(
        "projects/<int:pk>/list/",
        views.ProjectListModeView.as_view(),
        name="project_list_view",
    ),
    path(
        "projects/<int:pk>/settings/",
        views.ProjectUpdateView.as_view(),
        name="project_settings",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path(
        "projects/<int:pk>/columns/add/",
        views.create_column,
        name="column_create",
    ),
    path(
        "projects/<int:pk>/columns/<int:column_id>/edit/",
        views.update_column,
        name="column_update",
    ),
    path(
        "projects/<int:pk>/columns/<int:column_id>/delete/",
        views.delete_column,
        name="column_delete",
    ),
    path(
        "projects/<int:pk>/columns/<int:column_id>/tasks/quick/",
        views.quick_create_task,
        name="quick_create_task",
    ),
    path(
        "projects/<int:project_pk>/tasks/new/",
        views.TaskCreateView.as_view(),
        name="task_create",
    ),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path(
        "tasks/<int:pk>/delete/",
        views.TaskDeleteView.as_view(),
        name="task_delete",
    ),
    path(
        "tasks/<int:pk>/checklist/",
        views.add_checklist_item,
        name="checklist_add",
    ),
    path(
        "tasks/<int:pk>/checklist/<int:item_id>/toggle/",
        views.toggle_checklist_item,
        name="checklist_toggle",
    ),
    path(
        "tasks/<int:pk>/checklist/<int:item_id>/delete/",
        views.delete_checklist_item,
        name="checklist_delete",
    ),
    path("tasks/<int:pk>/comments/", views.add_comment, name="comment_add"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("api/tasks/reorder/", views.TaskReorderView.as_view(), name="task_reorder"),
]
