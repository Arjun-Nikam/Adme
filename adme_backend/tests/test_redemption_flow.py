"""
Redemption flow — Stories CON-1 (scan), CON-2 (near-me), CON-3 (points),
CON-4 (profile), MER-5 (match + approve).
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.consumers.models import Consumer, MerchantLoyaltyPoints, Redemption
from apps.merchants.models import Campaign, Category, Merchant, Offer


@pytest.fixture
def world(db):
    cat = Category.objects.create(name="Food")
    m_user = User.objects.create_user(
        username="m@x", email="m@x", password="pw-test-1234", role=User.Role.MERCHANT
    )
    merchant = Merchant.objects.create(
        user=m_user, business_name="Diner", contact_person="C",
        store_address="A", latitude="12.971600", longitude="77.594600",
        category=cat, total_redemptions=0,
    )
    campaign = Campaign.objects.create(
        merchant=merchant, title="C", start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=10),
        status=Campaign.Status.ACTIVE,
    )
    offer = Offer.objects.create(
        merchant=merchant, campaign=campaign, offer_code="DEMO-1",
        title="20% off", discount_value=20,
    )
    c_user = User.objects.create_user(
        username="c@x", email="c@x", password="pw-test-1234", role=User.Role.CONSUMER
    )
    consumer = Consumer.objects.create(user=c_user, adme_points_balance=0)
    return {
        "merchant": merchant, "m_user": m_user, "offer": offer,
        "consumer": consumer, "c_user": c_user,
    }


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.mark.django_db
def test_full_scan_match_approve_awards_points(world):
    consumer_c = client_for(world["c_user"])
    merchant_c = client_for(world["m_user"])

    # CON-1 scan
    res = consumer_c.post(
        reverse("redemption-scan"), {"offer_code": "DEMO-1"}, format="json"
    )
    assert res.status_code == 201
    rid = res.data["id"]
    assert res.data["match_status"] == "pending"
    world["consumer"].refresh_from_db()
    assert world["consumer"].adme_points_balance == 5  # scan reward

    # MER-5 match
    res = merchant_c.post(
        reverse("redemption-match"), {"offer_code": "DEMO-1"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["match_status"] == "matched"

    # approve before match is impossible now; approve after match:
    res = merchant_c.post(reverse("redemption-approve", args=[rid]))
    assert res.status_code == 200
    assert res.data["approval_status"] == "approved"

    r = Redemption.objects.get(pk=rid)
    assert r.approved_by_id == world["m_user"].id and r.approved_at is not None
    assert r.offer.status == "redeemed"
    world["merchant"].refresh_from_db()
    assert world["merchant"].total_redemptions == 1
    world["consumer"].refresh_from_db()
    assert world["consumer"].adme_points_balance == 25  # 5 + 20
    mlp = MerchantLoyaltyPoints.objects.get(
        consumer=world["consumer"], merchant=world["merchant"]
    )
    assert mlp.points_balance == 10


@pytest.mark.django_db
def test_approve_requires_match(world):
    consumer_c = client_for(world["c_user"])
    merchant_c = client_for(world["m_user"])
    rid = consumer_c.post(
        reverse("redemption-scan"), {"offer_code": "DEMO-1"}, format="json"
    ).data["id"]
    res = merchant_c.post(reverse("redemption-approve", args=[rid]))
    assert res.status_code == 400


@pytest.mark.django_db
def test_other_merchant_cannot_match_or_approve(world):
    other = User.objects.create_user(
        username="m2@x", password="pw-test-1234", role=User.Role.MERCHANT
    )
    Merchant.objects.create(
        user=other, business_name="Other", contact_person="C",
        store_address="A", latitude="1", longitude="1",
    )
    client_for(world["c_user"]).post(
        reverse("redemption-scan"), {"offer_code": "DEMO-1"}, format="json"
    )
    res = client_for(other).post(
        reverse("redemption-match"), {"offer_code": "DEMO-1"}, format="json"
    )
    assert res.status_code == 400  # no pending redemption at *their* store


@pytest.mark.django_db
def test_scan_unknown_code_is_400(world):
    res = client_for(world["c_user"]).post(
        reverse("redemption-scan"), {"offer_code": "NOPE"}, format="json"
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_consumer_profile_and_history(world):
    consumer_c = client_for(world["c_user"])
    consumer_c.post(
        reverse("redemption-scan"), {"offer_code": "DEMO-1"}, format="json"
    )
    prof = consumer_c.get(reverse("consumer-me"))
    assert prof.status_code == 200
    assert prof.data["adme_points_balance"] == 5
    assert prof.data["totals"]["redemptions_total"] == 1
    assert prof.data["redemptions"][0]["offer_code"] == "DEMO-1"

    mine = consumer_c.get(reverse("redemption-mine"))
    assert mine.status_code == 200 and len(mine.data) == 1


@pytest.mark.django_db
def test_near_me_sorts_by_distance_and_respects_radius(world):
    far_user = User.objects.create_user(
        username="mf@x", password="pw-test-1234", role=User.Role.MERCHANT
    )
    far = Merchant.objects.create(
        user=far_user, business_name="Far", contact_person="C", store_address="A",
        latitude="13.100000", longitude="77.700000",
    )
    camp = Campaign.objects.create(
        merchant=far, title="C", start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=5),
        status=Campaign.Status.ACTIVE,
    )
    Offer.objects.create(
        merchant=far, campaign=camp, offer_code="FAR-1", title="Far offer",
        discount_value=5,
    )
    c = client_for(world["c_user"])
    near = c.get(
        reverse("offer-near-me"),
        {"lat": "12.9716", "lng": "77.5946", "radius_km": "1"},
    )
    assert near.status_code == 200
    codes = [row["offer_code"] for row in near.data]
    assert codes == ["DEMO-1"]  # far one is outside 1km

    wide = c.get(
        reverse("offer-near-me"),
        {"lat": "12.9716", "lng": "77.5946", "radius_km": "3"},
    )
    assert wide.data[0]["offer_code"] == "DEMO-1"  # nearest first
    assert wide.data[0]["distance_km"] <= wide.data[-1]["distance_km"]


@pytest.mark.django_db
def test_near_me_rejects_bad_radius(world):
    res = client_for(world["c_user"]).get(
        reverse("offer-near-me"),
        {"lat": "12.9", "lng": "77.5", "radius_km": "7"},
    )
    assert res.status_code == 400
