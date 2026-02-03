from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

# =========================
# Base + env
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# Comma separated hosts in .env
ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",") if h.strip()]

# Helpful defaults for deployment (safe even if unused)
# Add these to .env later for Render/Railway
# e.g. DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,interntrack.onrender.com
ALLOWED_HOSTS += [
    ".onrender.com",
    ".up.railway.app",
    ".trycloudflare.com",
    ".ngrok-free.app",
    "codavatarinterntracking-api.onrender.com"
]

# =========================
# Apps
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    "accounts",
    "internships",
]

# =========================
# Middleware
# =========================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    # ✅ WhiteNoise MUST be right after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "CodavatarInternTracking.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "CodavatarInternTracking.wsgi.application"

# =========================
# ✅ MySQL via PyMySQL
# =========================
# IMPORTANT:
# pip install pymysql cryptography
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", ""),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}


# =========================
# Auth
# =========================
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# =========================
# Internationalization
# =========================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# =========================
# Static files (Render/Railway friendly)
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================
# Sessions (fix admin session)
# =========================
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# =========================
# ✅ CORS + CSRF (Frontend hosting)
# =========================
# Set FRONTEND_URL in .env later when Netlify is ready
# Example: FRONTEND_URL=https://your-site.netlify.app
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500").strip()

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://codavatarinterntracking.netlify.app",
]
CSRF_TRUSTED_ORIGINS = [
    "https://codavatarinterntracking.netlify.app",
]
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]
if FRONTEND_URL and FRONTEND_URL not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

CSRF_TRUSTED_ORIGINS = []
# CSRF requires full scheme (http/https) - add only if valid
for url in CORS_ALLOWED_ORIGINS:
    if url.startswith("http://") or url.startswith("https://"):
        CSRF_TRUSTED_ORIGINS.append(url)

# =========================
# ✅ DRF + JWT
# =========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.jwt_auth.TokenVersionJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# =========================
# Email
# =========================
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@codavatar.tech")

# Used for reset links
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", FRONTEND_URL)
