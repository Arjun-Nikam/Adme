"""
Root URL conf. Every module gets its own /api/v1/<module>/ namespace so the
API mirrors apps/ 1:1 — see docs/architecture.md for the full URL scheme.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    AdmeTokenObtainPairView,
    MeView,
    customer_signup_request,
    customer_signup_verify,
)
from common.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health / ops
    path("healthz/", healthz, name="healthz"),

    # API schema (drf-spectacular)
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Auth
    path(
        "api/v1/auth/login/",
        AdmeTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/v1/auth/signup/request-otp/", customer_signup_request, name="customer-signup-request"),
    path("api/v1/auth/signup/verify-otp/", customer_signup_verify, name="customer-signup-verify"),

    # Module APIs (one include per Django app — see docs/architecture.md)
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/merchants/", include("apps.merchants.urls")),
    path("api/v1/consumers/", include("apps.consumers.urls")),
    path("api/v1/rickshaws/", include("apps.rickshaws.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/admin-ops/", include("apps.admin_ops.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
