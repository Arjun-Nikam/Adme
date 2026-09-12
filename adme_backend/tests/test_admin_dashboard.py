"""Story ADM-1 — advertiser directory + live fleet + live-rickshaw recency."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.merchants.models import Campaign, Merchant
from apps.rickshaws.models import GpsPing, Rickshaw


def _admin():
    return User.objects.create_user(
        username="a1", password="pw-test-1234", role=User.Role.ADMIN
    )


def _merchant_with_campaign():
    user = User.objects.create_user(
        username="m1", password="pw-test-1234", role=User.Role.MERCHANT
    )
    merchant = Merchant.objects.create(
        user=user,
        business_name="Acme Foods",
        contact_person="C",
        store_address="A",
        latitude=1,
        longitude=1,
        total_redemptions=7,
    )
    Campaign.objects.create(
        merchant=merchant,
        title="Live one",
        start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=10),
        status=Campaign.Status.ACTIVE,
    )
    return merchant


def _rickshaw(reg, ping_age_minutes, status=Rickshaw.Status.ACTIVE):
    r = Rickshaw.objects.create(registration_number=reg, status=status)
    if ping_age_minutes is not None:
        GpsPing.objects.create(
            rickshaw=r,
            latitude=12.9,
            longitude=77.5,
            recorded_at=timezone.now() - timedelta(minutes=ping_age_minutes),
        )
    return r


@pytest.mark.django_db
def test_advertiser_directory_lists_merchants_with_counts():
    _merchant_with_campaign()
    client = APIClient()
    client.force_authenticate(user=_admin())
    res = client.get(reverse("advertiser-directory"))
    assert res.status_code == 200
    row = res.data[0]
    assert row["business_name"] == "Acme Foods"
    assert row["active_campaigns"] == 1
    assert row["total_redemptions"] == 7
    assert "spend" in row


@pytest.mark.django_db
def test_advertiser_directory_requires_admin():
    consumer = User.objects.create_user(
        username="c1", password="pw-test-1234", role=User.Role.CONSUMER
    )
    client = APIClient()
    client.force_authenticate(user=consumer)
    assert client.get(reverse("advertiser-directory")).status_code == 403


@pytest.mark.django_db
def test_live_fleet_and_overview_respect_recency():
    _rickshaw("KA01AB0001", ping_age_minutes=2)  # live
    _rickshaw("KA01AB0002", ping_age_minutes=90)  # stale
    _rickshaw("KA01AB0003", ping_age_minutes=None)  # never pinged
    _rickshaw("KA01AB0004", ping_age_minutes=1, status=Rickshaw.Status.INACTIVE)

    client = APIClient()
    client.force_authenticate(user=_admin())

    fleet = client.get(reverse("live-fleet")).data
    # inactive rickshaw is excluded entirely; 3 active listed
    assert {r["registration_number"] for r in fleet} == {
        "KA01AB0001",
        "KA01AB0002",
        "KA01AB0003",
    }
    live_flags = {r["registration_number"]: r["is_live"] for r in fleet}
    assert live_flags["KA01AB0001"] is True
    assert live_flags["KA01AB0002"] is False
    assert live_flags["KA01AB0003"] is False

    overview = client.get(reverse("platform-overview")).data
    assert overview["total_live_rickshaws"] == 1
