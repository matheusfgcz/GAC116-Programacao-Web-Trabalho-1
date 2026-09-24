"""ASGI config for FlowTask."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowtask.settings")

application = get_asgi_application()
