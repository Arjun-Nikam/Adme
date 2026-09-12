"""Consumer module models — Dev Plan Section 5.3 (RD Section 3)."""
from django.conf import settings
from django.db import models
from common.models import TimeStampedModel
from apps.merchants.models import Merchant, Offer


class Consumer(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consumer_profile")
    adme_points_balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


class MerchantLoyaltyPoints(TimeStampedModel):
    """Per-merchant points, redeemable only at that merchant (RD 3)."""
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="merchant_points")
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="loyalty_points")
    points_balance = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("consumer", "merchant")


class Redemption(TimeStampedModel):
    """RD 2.6/2.7/3 — the central record for offer matching + approval."""

    class MatchStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        MATCHED = "matched", "Matched"
        MISMATCHED = "mismatched", "Mismatched"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="redemptions")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="redemptions")
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="redemptions")
    scan_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    scan_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    store_visit_confirmed = models.BooleanField(default=False)
    match_status = models.CharField(max_length=20, choices=MatchStatus.choices, default=MatchStatus.PENDING)
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_redemptions"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
