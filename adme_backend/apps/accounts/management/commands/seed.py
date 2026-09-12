"""
Local-dev / UAT seed data (Dev Plan Phase 0). Idempotent — safe to re-run.

Creates, so login + the dashboards show real data immediately:
  - one user per RD role (password: "adme-dev-1234"), usernames <role>@adme.local
  - the RD 2.8 category list + one demo Plan
  - a Merchant profile for merchant@adme.local, with an active Campaign and
    ~30 days of CampaignMetric rows
  - a Consumer, a Driver, 3 active Rickshaws
  - a handful of approved Redemptions spread across the day

Do NOT run against production.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.consumers.models import Consumer, MerchantLoyaltyPoints, Redemption
from apps.merchants.models import (
    Campaign,
    CampaignMetric,
    Category,
    Merchant,
    Offer,
    Plan,
)
from apps.rickshaws.models import Driver, GpsPing, HardwareUnit, Rickshaw

DEV_PASSWORD = "adme-dev-1234"
CATEGORIES = ["Food", "Drinks", "Clothing", "Fashion", "Saloon", "Jewellery"]


class Command(BaseCommand):
    help = "Seed local development data (roles, categories, demo dashboard data)."

    @transaction.atomic
    def handle(self, *args, **options):
        rnd = random.Random(42)
        users = {}
        for role, _label in User.Role.choices:
            username = f"{role}@adme.local"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": username,
                    "role": role,
                    "is_staff": role == "super_admin",
                    "is_superuser": role == "super_admin",
                },
            )
            if created:
                user.set_password(DEV_PASSWORD)
                user.save()
                self.stdout.write(f"  + user {username} ({role})")
            users[role] = user

        for name in CATEGORIES:
            Category.objects.get_or_create(name=name)
        category = Category.objects.get(name="Food")

        plan, _ = Plan.objects.get_or_create(
            name="Starter (demo)",
            defaults={
                "duration_days": 30,
                "ad_view_cap": 20000,
                "geographic_reach_km": 5,
                "price": 4999,
            },
        )

        merchant, _ = Merchant.objects.get_or_create(
            user=users["merchant"],
            defaults={
                "business_name": "Demo Diner",
                "contact_person": "Priya R.",
                "store_address": "12 MG Road, Bengaluru",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "category": category,
                "plan": plan,
                "contract_expiry_date": timezone.localdate() + timedelta(days=20),
            },
        )

        campaign, _ = Campaign.objects.get_or_create(
            merchant=merchant,
            title="Monsoon Combo",
            defaults={
                "start_date": timezone.localdate() - timedelta(days=30),
                "end_date": timezone.localdate() + timedelta(days=15),
                "status": Campaign.Status.ACTIVE,
            },
        )

        offer, _ = Offer.objects.get_or_create(
            offer_code="DEMO-COMBO-20",
            defaults={
                "merchant": merchant,
                "campaign": campaign,
                "title": "20% off the combo meal",
                "discount_value": 20,
            },
        )
        # still-active offers: FRESH-10 for the scan->match->approve demo,
        # NEARBY-15 stays active so "near me" always returns something.
        for code, title, disc in (
            ("DEMO-FRESH-10", "Flat 10% today", 10),
            ("DEMO-NEARBY-15", "15% off for nearby riders", 15),
        ):
            Offer.objects.get_or_create(
                offer_code=code,
                defaults={
                    "merchant": merchant,
                    "campaign": campaign,
                    "title": title,
                    "discount_value": disc,
                },
            )

        today = timezone.localdate()
        made = 0
        for i in range(30):
            day = today - timedelta(days=29 - i)
            base = 300 + i * 12
            _, created = CampaignMetric.objects.get_or_create(
                campaign=campaign,
                date=day,
                defaults={
                    "ad_views": base * 20 + rnd.randint(-200, 200),
                    "qr_scans": base // 2 + rnd.randint(-15, 15),
                    "offers_saved": base // 6 + rnd.randint(-5, 5),
                    "store_visits": base // 12 + rnd.randint(-3, 3),
                    "offers_redeemed": base // 20 + rnd.randint(-2, 2),
                },
            )
            made += int(created)
        if made:
            self.stdout.write(f"  + {made} CampaignMetric rows")

        consumer, _ = Consumer.objects.get_or_create(
            user=users["consumer"], defaults={"adme_points_balance": 120}
        )

        hw, _ = HardwareUnit.objects.get_or_create(
            serial_number="HW-DEMO-0001",
            defaults={"model": "AdmeScreen v1", "status": HardwareUnit.Status.ONLINE},
        )
        driver, _ = Driver.objects.get_or_create(
            user=users["driver"],
            defaults={
                "license_number": "KA01-2020-0001",
                "vehicle_rc_number": "RC-DEMO-0001",
                "kyc_status": Driver.KycStatus.APPROVED,
            },
        )
        for n in range(1, 4):
            rickshaw, _ = Rickshaw.objects.get_or_create(
                registration_number=f"KA01AB{1000 + n}",
                defaults={
                    "merchant": merchant,
                    "driver": driver,
                    "hardware_unit": hw if n == 1 else None,
                    "status": Rickshaw.Status.ACTIVE,
                },
            )
            if rickshaw.merchant_id != merchant.id:
                rickshaw.merchant = merchant
                rickshaw.save(update_fields=["merchant", "updated_at"])
            if not rickshaw.gps_pings.exists():
                # rickshaws 1 & 2 pinged just now (live); 3 went quiet an hour ago
                age = timedelta(minutes=2) if n < 3 else timedelta(hours=1)
                GpsPing.objects.create(
                    rickshaw=rickshaw,
                    latitude=12.9716 + n * 0.01,
                    longitude=77.5946 + n * 0.01,
                    recorded_at=timezone.now() - age,
                )

        if not Redemption.objects.filter(merchant=merchant).exists():
            now_local = timezone.localtime(timezone.now())
            for hour in (9, 10, 13, 14, 15, 18, 19, 20, 22):
                approved = now_local.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                ) - timedelta(days=rnd.randint(0, 20))
                Redemption.objects.create(
                    consumer=consumer,
                    offer=offer,
                    merchant=merchant,
                    store_visit_confirmed=True,
                    match_status=Redemption.MatchStatus.MATCHED,
                    approval_status=Redemption.ApprovalStatus.APPROVED,
                    approved_by=users["merchant"],
                    approved_at=approved,
                )
            merchant.total_redemptions = Redemption.objects.filter(
                merchant=merchant, approval_status="approved"
            ).count()
            merchant.save(update_fields=["total_redemptions"])
            MerchantLoyaltyPoints.objects.get_or_create(
                consumer=consumer,
                merchant=merchant,
                defaults={"points_balance": 90},
            )
            consumer.adme_points_balance = 300
            consumer.save(update_fields=["adme_points_balance"])
            offer.status = Offer.Status.REDEEMED
            offer.save(update_fields=["status"])
            self.stdout.write("  + 9 approved Redemptions + loyalty points")

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(f"All dev users share the password: {DEV_PASSWORD}")
