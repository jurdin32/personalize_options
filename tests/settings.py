"""Los ajustes con los que se prueban el paquete.

Solo lo que necesita una app de Django: el admin, los usuarios y una base de datos
en memoria. No depende de ningún proyecto.
"""

SECRET_KEY = "solo-para-las-pruebas"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "personalize_options",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "personalize_options.middleware.PermisosMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

STATIC_URL = "static/"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Los ajustes del paquete (ver src/personalize_options/conf.py).
PERSONALIZE_OPTIONS = {
    "MODO": "abierto",
    "SUPERUSUARIOS_TODO": True,
}
