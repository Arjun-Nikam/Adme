"""
Story MER-3 (merchant dashboard) + ADM-1 (platform overview) + CORE-2
(deactivate locks out). These are the login+dashboard slice.
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consumers.models import Consumer
from apps.merchants.models import Campaign, CampaignMetric, Merchant


def _merchant_user(username="m1"):
    user = User.objects.create_user(
        username=username, password="pw-test-1234", role=User.Role.MERCHANT
    )
    merchant = Merchant.objects.create(
        user=user,
        business_name=f"Biz {username}",
        contact_person="C",
        store_address="A",
        latitude=1,
        longitude=1,
    )
    return user, merchant


def _metrics(merchant, days=5, per_day=100):
    campaign = Campaign.objects.create(
        merchant=merchant,
        title="C",
        start_date=timezone.localdate() - timedelta(days=days),
        end_date=timezone.localdate() + timedelta(days=5),
        status=Campaign.Status.ACTIVE,
    )
    today = timezone.localdate()
    for i in range(days):
        CampaignMetric.objects.create(
            campaign=campaign,
            date=today - timedelta(days=i),
            ad_views=per_day,
            qr_scans=10,
            offers_saved=5,
            store_visits=3,
            offers_redeemed=2,
        )
    return campaign


@pytest.mark.django_db
def test_merchant_dashboard_totals_and_series():
    user, merchant = _merchant_user()
    _metrics(merchant, days=5, per_day=100)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get(
        reverse("merchant-dashboard", args=[merchant.id]), {"start": "2000-01-01"}
    )

    assert res.status_code == 200
    body = res.data
    assert body["totals"]["ad_views"] == 500
    assert body["totals"]["offers_redeemed"] == 10
    assert len(body["time_series"]) == 5
    assert {"label", "value"} <= set(body["redemption_breakdown"][0].keys())


@pytest.mark.django_db
def test_merchant_cannot_see_other_merchants_dashboard():
    _u1, m1 = _merchant_user("m1")
    u2, _m2 = _merchant_user("m2")

    client = APIClient()
    client.force_authenticate(user=u2)
    res = client.get(reverse("merchant-dashboard", args=[m1.id]))
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_can_read_any_merchant_dashboard():
    _u1, m1 = _merchant_user("m1")
    admin = User.objects.create_user(
        username="a1", password="pw-test-1234", role=User.Role.ADMIN
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    res = client.get(reverse("merchant-dashboard", args=[m1.id]))
    assert res.status_code == 200


@pytest.mark.django_db
def test_platform_overview_requires_admin():
    consumer_user = User.objects.create_user(
        username="c1", password="pw-test-1234", role=User.Role.CONSUMER
    )
    Consumer.objects.create(user=consumer_user)
    admin = User.objects.create_user(
        username="a1", password="pw-test-1234", role=User.Role.ADMIN
    )
    url = reverse("platform-overview")

    client = APIClient()
    client.force_authenticate(user=consumer_user)
    assert client.get(url).status_code == 403

    client.force_authenticate(user=admin)
    ok = client.get(url)
    assert ok.status_code == 200
    assert "total_live_rickshaws" in ok.data


@pytest.mark.django_db
def test_me_returns_merchant_id():
    user, merchant = _merchant_user()
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get(reverse("auth-me"))
    assert res.data["merchant_id"] == merchant.id
    assert res.data["consumer_id"] is None


@pytest.mark.django_db
def test_deactivated_user_cannot_log_in():
    User.objects.create_user(
        username="gone@adme.local",
        email="gone@adme.local",
        password="pw-test-1234",
        role=User.Role.MERCHANT,
        is_active=False,
    )
    client = APIClient()
    res = client.post(
        reverse("token_obtain_pair"),
        {"username": "gone@adme.local", "password": "pw-test-1234"},
        format="json",
    )
    assert res.status_code == 401
