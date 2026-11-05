from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="aluno", password="aluno1234")

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FlowTask")

    def test_register_page_renders(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "aluno", "password": "aluno1234"},
        )
        self.assertEqual(response.status_code, 302)
