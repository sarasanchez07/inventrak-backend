"""
Django settings for InvenTrack project.

Sistema de Gestión de Inventarios
Backend con Django + Django REST Framework
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta
from corsheaders.defaults import default_headers
import sys

TESTING = "test" in sys.argv

# --------------------------------------------------
# BASE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno
load_dotenv(BASE_DIR / '.env')

# --------------------------------------------------
# SEGURIDAD
# --------------------------------------------------

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,backend-inventrack.onrender.com").split(",")
    if host.strip()
]

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# --------------------------------------------------
# APLICACIONES
# --------------------------------------------------

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "django_filters",

    # Apps locales (InvenTrack)
    "apps.authentication",
    "apps.inventory",
    "apps.movements",   
    "apps.reports",
    "apps.alerts",
    "apps.dashboard",
]

# --------------------------------------------------
# USUARIO PERSONALIZADO
# --------------------------------------------------

AUTH_USER_MODEL = "authentication.User"

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# URLS / WSGI
# --------------------------------------------------

ROOT_URLCONF = "inventrack.urls"

WSGI_APPLICATION = "inventrack.wsgi.application"

# --------------------------------------------------
# TEMPLATES (opcional, por si usas admin o emails)
# --------------------------------------------------

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
            ],
        },
    },
]

# --------------------------------------------------
# BASE DE DATOS
# --------------------------------------------------

# SQLite para tests, PostgreSQL para desarrollo/producción
if "test" in sys.argv or "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_password = os.getenv("DB_PASSWORD")
        if not db_password:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("DB_PASSWORD o DATABASE_URL no está configurada en el entorno")
        
        db_url = f"postgres://{os.getenv('DB_USER', 'postgres')}:{db_password}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'inventrack_db')}"

    DATABASES = {
        "default": dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# --------------------------------------------------
# VALIDADORES DE CONTRASEÑA
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------
# INTERNACIONALIZACIÓN
# --------------------------------------------------

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# ARCHIVOS ESTÁTICOS Y MEDIA
# --------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# --------------------------------------------------
# JWT
# --------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------
# SWAGGER / OPENAPI
# --------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "InvenTrack API",
    "DESCRIPTION": "Documentación oficial de la API del sistema de gestión de inventarios InvenTrack",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "TAGS_SORTER": "alpha",
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]|/auth'
}

# --------------------------------------------------
# CORS (Frontend separado)
# --------------------------------------------------

import logging
logger = logging.getLogger(__name__)

CORS_ALLOWED_ORIGINS = []
_raw_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,https://inventrack-fmud.vercel.app",
).split(",")

for _origin in _raw_origins:
    _origin = _origin.strip()
    if not _origin:
        continue
    if _origin.startswith("http://") or _origin.startswith("https://"):
        CORS_ALLOWED_ORIGINS.append(_origin)
    else:
        logger.warning(f"CORS origin ignorado por formato inválido: {_origin}. Debe empezar con http:// o https://")

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False").lower() == "true"
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization"]

# --------------------------------------------------
# EMAIL (opcional – recuperación de contraseña)
# --------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
#EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
#EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
#EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
#EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
#EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
#DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# --------------------------------------------------
# FRONTEND
# --------------------------------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
