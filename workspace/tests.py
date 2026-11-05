from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from workspace.models import Project, StatusColumn, Task


class WorkspaceSmokeTests(TestCase):
    """Testes básicos alinhados ao suporte a testes do Django."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="teste",
            password="teste1234",
            first_name="Teste",
        )
        self.project = Project.objects.create(
            name="Projeto Teste",
            owner=self.user,
            description="Projeto para testes automatizados",
        )
        self.project.members.add(self.user)
        self.project.seed_default_columns()
        self.column = self.project.columns.first()
        self.task = Task.objects.create(
            project=self.project,
            column=self.column,
            title="Tarefa de teste",
            created_by=self.user,
            assignee=self.user,
        )
        self.client = Client()

    def test_model_str_methods(self):
        self.assertIn("Projeto Teste", str(self.project))
        self.assertIn("A Fazer", str(self.column))
        self.assertIn("Tarefa de teste", str(self.task))

    def test_default_columns_seeded(self):
        names = set(self.project.columns.values_list("name", flat=True))
        self.assertEqual(names, {"A Fazer", "Em Progresso", "Concluído"})

    def test_login_required_dashboard(self):
        response = self.client.get(reverse("workspace:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_authenticated(self):
        self.client.login(username="teste", password="teste1234")
        response = self.client.get(reverse("workspace:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Projeto Teste")

    def test_board_view(self):
        self.client.login(username="teste", password="teste1234")
        response = self.client.get(
            reverse("workspace:project_board", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-kanban")
        self.assertContains(response, "Tarefa de teste")

    def test_task_detail_drawer(self):
        self.client.login(username="teste", password="teste1234")
        response = self.client.get(
            reverse("workspace:task_detail", kwargs={"pk": self.task.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "drawer-root")
