"""
Phase 0 smoke tests — keep CI green from the first push and give new devs a
working example to copy. Real per-story tests live next to their app.
"""
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User


def test_django_check_passes():
    """`manage.py check` must pass with zero issues."""
    call_command("check")


@pytest.mark.django_db
def test_user_model_roles_create():
    """The single users table accepts every RD role."""
    for role, _ in User.Role.choices:
        User.objects.create_user(
            username=f"{role}_user", password="pw-test-1234", role=role
        )
    assert User.objects.count() == len(User.Role.choices)


@pytest.mark.django_db
def test_login_returns_role_claim():
    """CORE-1: the JWT returned by /auth/login/ must carry the user's role."""
    User.objects.create_user(
        username="merchant1",
        email="merchant1@example.com",
        password="pw-test-1234",
        role=User.Role.MERCHANT,
    )
    client = APIClient()
    res = client.post(
        reverse("token_obtain_pair"),
        {"username": "merchant1", "password": "pw-test-1234"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["role"] == "merchant"


@pytest.mark.django_db
def test_me_endpoint_returns_current_user():
    """/auth/me/ powers the client bootstrap after login."""
    user = User.objects.create_user(
        username="admin1", password="pw-test-1234", role=User.Role.ADMIN
    )
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get(reverse("auth-me"))
    assert res.status_code == 200
    assert res.data["role"] == "admin"
    assert res.data["username"] == "admin1"
