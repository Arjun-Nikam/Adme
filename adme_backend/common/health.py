"""Liveness/readiness probe (B16). Unauthenticated, cheap, no side effects."""
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    checks = {"app": "ok"}
    status = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["db"] = "ok"
    except Exception:  # noqa: BLE001
        checks["db"] = "error"
        status = 503
    return JsonResponse(checks, status=status)
