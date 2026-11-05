from django.contrib import admin

from .models import (
    ChecklistItem,
    Comment,
    Project,
    ProjectMembership,
    StatusColumn,
    Task,
)

admin.site.site_header = "FlowTask — Administração"
admin.site.site_title = "FlowTask Admin"
admin.site.index_title = "Gestão de projetos e tarefas"


class StatusColumnInline(admin.TabularInline):
    model = StatusColumn
    extra = 0


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    autocomplete_fields = ("user",)


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "color", "created_at", "updated_at")
    list_filter = ("owner", "created_at", "color")
    search_fields = ("name", "description", "owner__username")
    filter_horizontal = ("members",)
    inlines = [StatusColumnInline, ProjectMembershipInline]
    date_hierarchy = "created_at"


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role", "joined_at")
    list_filter = ("role", "project", "joined_at")
    search_fields = ("user__username", "project__name")
    list_editable = ("role",)
    autocomplete_fields = ("user", "project")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "column",
        "priority",
        "assignee",
        "due_date",
        "position",
        "updated_at",
    )
    list_filter = (
        "priority",
        "project",
        "column",
        "due_date",
        "assignee",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("title", "description", "assignee__username")
    list_editable = ("priority", "position")
    inlines = [ChecklistItemInline, CommentInline]
    date_hierarchy = "created_at"
    autocomplete_fields = ("project", "column", "assignee", "created_by")


@admin.register(StatusColumn)
class StatusColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "order", "color")
    list_filter = ("project", "name")
    search_fields = ("name", "project__name")
    list_editable = ("order",)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("text", "task", "done", "order")
    list_filter = ("done", "task__project")
    search_fields = ("text", "task__title")
    list_editable = ("done", "order")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    list_filter = ("created_at", "author", "task__project")
    search_fields = ("body", "task__title", "author__username")
    readonly_fields = ("created_at",)
