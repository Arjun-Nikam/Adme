"""Merchant application -> admin approval -> merchant ad launch."""
from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.merchants.models import Merchant


@pytest.mark.django_db
def test_merchant_application_requires_admin_approval():
    admin = User.objects.create_user(username="ops", password="pw-test-1234", role=User.Role.ADMIN)
    public_client = APIClient()

    response = public_client.post(reverse("merchant-apply"), {
        "username": "new-merchant",
        "email": "merchant@example.com",
        "password": "merchant-password",
        "business_name": "Fresh Foods",
        "contact_person": "Asha",
        "store_address": "12 Market Road",
        "latitude": "12.971600",
        "longitude": "77.594600",
    }, format="json")

    assert response.status_code == 201
    merchant = Merchant.objects.get(business_name="Fresh Foods")
    assert merchant.user.role == User.Role.MERCHANT
    assert merchant.approval_status == Merchant.ApprovalStatus.PENDING
    assert merchant.user.is_active is False
    assert merchant.user.check_password("merchant-password")
    assert response.data["merchant_id"] == merchant.id

    pending_client = APIClient()
    pending_client.force_authenticate(user=merchant.user)
    blocked = pending_client.post(reverse("campaign-launch"), {
        "title": "Blocked ad",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=7)),
        "offer_code": "PENDING10",
        "offer_title": "Pending offer",
        "discount_value": "10.00",
    }, format="json")
    assert blocked.status_code == 403

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin)
    approved = admin_client.post(
        reverse("merchant-verification-approve", args=[merchant.id])
    )
    assert approved.status_code == 200
    merchant.refresh_from_db()
    assert merchant.approval_status == Merchant.ApprovalStatus.APPROVED
    assert merchant.user.is_active is True


@pytest.mark.django_db
def test_merchant_launch_is_visible_only_while_campaign_is_live():
    merchant_user = User.objects.create_user(
        username="merchant", password="pw-test-1234", role=User.Role.MERCHANT
    )
    merchant = Merchant.objects.create(
        user=merchant_user,
        business_name="Fresh Foods",
        contact_person="Asha",
        store_address="12 Market Road",
        latitude=12.9716,
        longitude=77.5946,
        approval_status=Merchant.ApprovalStatus.APPROVED,
    )
    merchant_client = APIClient()
    merchant_client.force_authenticate(user=merchant_user)

    response = merchant_client.post(reverse("campaign-launch"), {
        "title": "Lunch special",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=7)),
        "offer_code": "FRESH10",
        "offer_title": "10 percent off lunch",
        "description": "Valid at the Market Road store.",
        "discount_value": "10.00",
    }, format="json")
    assert response.status_code == 201

    consumer = User.objects.create_user(
        username="consumer", password="pw-test-1234", role=User.Role.CONSUMER
    )
    consumer_client = APIClient()
    consumer_client.force_authenticate(user=consumer)
    live = consumer_client.get(reverse("campaign-live"))

    assert live.status_code == 200
    assert live.data[0]["merchant"] == merchant.business_name
    assert live.data[0]["offers"][0]["offer_code"] == "FRESH10"
