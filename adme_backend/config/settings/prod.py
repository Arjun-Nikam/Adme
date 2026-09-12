from .base import *  # noqa
from .base import SECRET_KEY

DEBUG = False

# TLS / secure cookies
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True

# Fail fast if the deploy forgot to set a real secret.
if SECRET_KEY in ("", "change-me", "dev-secret-key-change-me"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set to a real value in production.")
