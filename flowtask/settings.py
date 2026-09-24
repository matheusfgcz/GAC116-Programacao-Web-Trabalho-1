"""Django settings for FlowTask."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-^%=!&bxbu2)0y1@al%@1+l$2ymdp*(0xm&-8zx+00vcks#&%+&"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "workspace",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "flowtask.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "workspace.context_processors.nav_projects",
                "accounts.context_processors.user_profile",
            ],
        },
    },
]

WSGI_APPLICATION = "flowtask.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "workspace:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

JAZZMIN_SETTINGS = {
    "site_title": "FlowTask Admin",
    "site_header": "FlowTask",
    "site_brand": "FlowTask",
    "welcome_sign": "Ambiente administrativo FlowTask",
    "copyright": "GAC116 — UFLA",
    "search_model": ["auth.User", "workspace.Project", "workspace.Task"],
    "topmenu_links": [
        {"name": "Site", "url": "workspace:dashboard", "new_window": False},
        {
            "name": "GitHub",
            "url": "https://github.com/matheusfgcz/GAC116-Programacao-Web-Trabalho-1",
            "new_window": True,
        },
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "custom_css": "css/admin_contrast.css",
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.UserProfile": "fas fa-id-badge",
        "workspace.Project": "fas fa-folder-open",
        "workspace.Task": "fas fa-tasks",
        "workspace.StatusColumn": "fas fa-columns",
        "workspace.ChecklistItem": "fas fa-check-square",
        "workspace.Comment": "fas fa-comments",
        "workspace.ProjectMembership": "fas fa-user-friends",
    },
    "order_with_respect_to": [
        "workspace",
        "accounts",
        "auth",
    ],
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-primary",
    "accent": "accent-teal",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "actions_sticky_top": True,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
