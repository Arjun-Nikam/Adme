"""
Merchant module models — see Dev Plan Section 5.2 for the full schema
reference (RD Section 2).
"""
from django.conf import settings
from django.db import models
from common.models import TimeStampedModel


class Category(TimeStampedModel):
    """RD 2.8 — Food, Drinks, Clothing, Fashion, Saloon, Jewellery, etc."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Plan(TimeStampedModel):
    """RD 2.9 — subscription tiers configured by Adme."""
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    ad_view_cap = models.PositiveIntegerField()
    geographic_reach_km = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Merchant(TimeStampedModel):
    """RD 2.4 — merchant onboarding + lifecycle tracking."""

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class RenewalStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRING_SOON = "expiring_soon", "Expiring Soon"
        EXPIRED = "expired", "Expired"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="merchant_profile")
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.APPROVED,
    )
    business_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    store_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="merchants")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, related_name="merchants")
    contract_expiry_date = models.DateField(null=True, blank=True)
    renewal_status = models.CharField(max_length=20, choices=RenewalStatus.choices, default=RenewalStatus.ACTIVE)
    total_redemptions = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.business_name


class AreaMapping(TimeStampedModel):
    """RD 2.10 — geofencing a merchant's campaign to zones/routes/rickshaw clusters."""
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="area_mappings")
    zone_name = models.CharField(max_length=255, blank=True)
    route_id = models.CharField(max_length=100, blank=True)
    rickshaw_cluster_id = models.CharField(max_length=100, blank=True)


class Campaign(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        PAUSED = "paused", "Paused"

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="campaigns")
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    def __str__(self):
        return f"{self.title} ({self.merchant.business_name})"


class Offer(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REDEEMED = "redeemed", "Redeemed"
        EXPIRED = "expired", "Expired"

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="offers")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="offers")
    offer_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f"{self.offer_code} - {self.title}"


class CampaignMetric(TimeStampedModel):
    """Daily rollup — columns match the weekly Excel report exactly (RD 2.2)."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="daily_metrics")
    date = models.DateField()
    ad_views = models.PositiveIntegerField(default=0)
    qr_scans = models.PositiveIntegerField(default=0)
    offers_saved = models.PositiveIntegerField(default=0)
    store_visits = models.PositiveIntegerField(default=0)
    offers_redeemed = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("campaign", "date")


class Report(TimeStampedModel):
    """RD 2.1 — weekly report generated + delivered via Email and WhatsApp."""
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="reports")
    period_start = models.DateField()
    period_end = models.DateField()
    file_url = models.URLField(blank=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_whatsapp = models.BooleanField(default=False)
