from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "seu.usuario",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Seu nome"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": "input", "placeholder": "voce@email.com"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "usuario",
            "password1": "mínimo 8 caracteres",
            "password2": "repita a senha",
        }
        labels = {
            "username": "Usuário",
            "password1": "Senha",
            "password2": "Confirmar senha",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "input")
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]
            if name in labels:
                field.label = labels[name]
