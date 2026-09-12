"""
Base Django settings for the Adme Ops Screen platform.
Shared by dev.py and prod.py — do not put environment-specific values here.
"""
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "django_celery_beat",

    # Adme apps — one per RD module (see README / dev plan Section 6.1)
    "apps.accounts",
    "apps.merchants",
    "apps.consumers",
    "apps.rickshaws",
    "apps.reports",
    "apps.notifications",
    "apps.analytics",
    "apps.admin_ops",
]

AUTH_USER_MODEL = "accounts.User"

# RD CORE-1: the login identifier may be a username, email, or phone number.
AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="adme_db"),
        "USER": config("DB_USER", default="adme_user"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- File storage (B3 / ADR 0002) ----
# dev/CI: local filesystem. staging/prod: set USE_S3=True + the AWS_* vars and
# reports (RD 2.1) + KYC docs (RD 5) land in S3-compatible object storage,
# served through short-lived signed URLs.
USE_S3 = config("USE_S3", default=False, cast=bool)
if USE_S3:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="") or None
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_QUERYSTRING_AUTH = True  # signed URLs
    AWS_DEFAULT_ACL = None

# ---- Logging (B16) — structured, level from env ----
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"}
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
}

# ---- DRF ----
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # B16 — baseline rate limiting (Dev Plan Phase 7). Tune per-endpoint later;
    # high-frequency device endpoints (GPS/heartbeat) get their own scope.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/min",
        "device_ingest": "120/min",
        "default_user": "1000/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Adme Ops Screen API",
    "DESCRIPTION": "Internal Ops Screen Module — see docs/architecture.md.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    # CORE-2: short access lifetime so a deactivated user loses API access
    # quickly; their refresh tokens are blacklisted on deactivation.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ---- CORS ----
# Expo web (Metro) dev server serves on :8081. Override per environment.
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in config(
        "CORS_ALLOWED_ORIGINS", default="http://localhost:8081,http://localhost:19006"
    ).split(",")
    if o.strip()
]

# ---- Celery ----
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TIMEZONE = TIME_ZONE

# B10 — scheduled-job anchors (times are in CELERY_TIMEZONE = Asia/Kolkata).
# DatabaseScheduler lets ops edit these in the admin; this dict is the
# checked-in default so a fresh environment has them without manual setup.
CELERY_BEAT_SCHEDULE = {
    "merchant-weekly-reports": {
        # RD 2.1 / Story MER-2 — every Monday 06:00 IST.
        "task": "apps.reports.tasks.generate_weekly_reports",
        "schedule": crontab(hour=6, minute=0, day_of_week="mon"),
    },
    "plan-expiry-alerts": {
        # RD 2.5 / Story MER-4 — daily 09:00 IST, fires for merchants exactly
        # 5 days from contract_expiry_date.
        "task": "apps.notifications.tasks.send_expiry_alerts",
        "schedule": crontab(hour=9, minute=0),
    },
    "hardware-heartbeat-sweep": {
        # RD 5 / Story RIK-4 — every 5 minutes, flip stale units offline.
        "task": "apps.rickshaws.tasks.check_heartbeats",
        "schedule": crontab(minute="*/5"),
    },
    "campaign-metrics-rollup": {
        # Dev Plan Phase 4 — nightly 02:00 IST daily rollup into CampaignMetric.
        "task": "apps.merchants.tasks.rollup_campaign_metrics",
        "schedule": crontab(hour=2, minute=0),
    },
}

# ---- WhatsApp / Email / Maps (used by apps.notifications, apps.reports) ----
WHATSAPP_API_URL = config("WHATSAPP_API_URL", default="")
WHATSAPP_API_TOKEN = config("WHATSAPP_API_TOKEN", default="")
GOOGLE_MAPS_API_KEY = config("GOOGLE_MAPS_API_KEY", default="")

EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
