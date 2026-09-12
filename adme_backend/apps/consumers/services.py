"""
Redemption flow business logic (RD 2.6 / 2.7 / 3 — Stories CON-1, CON-3, CON-4,
MER-5). Views stay thin and call these; the point/counter side effects all live
here so they can't drift between call sites.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.merchants.models import CampaignMetric, Merchant, Offer

from .models import Consumer, MerchantLoyaltyPoints, Redemption

ADME_POINTS_ON_SCAN = 5
ADME_POINTS_ON_REDEEM = 20
MERCHANT_POINTS_ON_REDEEM = 10


def redemption_summary(r):
    return {
        "id": r.id,
        "offer_code": r.offer.offer_code,
        "offer_title": r.offer.title,
        "merchant": r.merchant.business_name,
        "discount_value": float(r.offer.discount_value),
        "match_status": r.match_status,
        "approval_status": r.approval_status,
        "store_visit_confirmed": r.store_visit_confirmed,
        "created_at": r.created_at,
        "approved_at": r.approved_at,
    }


def scan_offer(consumer, offer_code, latitude=None, longitude=None):
    """Story CON-1 — consumer scans/enters an offer code -> pending Redemption."""
    try:
        offer = Offer.objects.select_related("merchant", "campaign").get(
            offer_code=offer_code
        )
    except Offer.DoesNotExist:
        raise ValidationError({"offer_code": "Unknown offer code."})

    if offer.status != Offer.Status.ACTIVE:
        raise ValidationError(
            {"offer_code": f"This offer is {offer.get_status_display().lower()}."}
        )

    with transaction.atomic():
        redemption = Redemption.objects.create(
            consumer=consumer,
            offer=offer,
            merchant=offer.merchant,
            scan_latitude=latitude,
            scan_longitude=longitude,
        )
        Consumer.objects.filter(pk=consumer.pk).update(
            adme_points_balance=F("adme_points_balance") + ADME_POINTS_ON_SCAN
        )
    return redemption


def match_offer(merchant, offer_code):
    """
    Story MER-5 (RD 2.6) — merchant enters the consumer's code; find the pending
    redemption for that code at THIS merchant and flag it matched.
    """
    redemption = (
        Redemption.objects.select_related("offer")
        .filter(
            offer__offer_code=offer_code,
            merchant=merchant,
            match_status=Redemption.MatchStatus.PENDING,
            approval_status=Redemption.ApprovalStatus.PENDING,
        )
        .order_by("created_at")
        .first()
    )
    if redemption is None:
        raise ValidationError(
            {"offer_code": "No pending redemption for this code at your store."}
        )
    if redemption.offer.status != Offer.Status.ACTIVE:
        redemption.match_status = Redemption.MatchStatus.MISMATCHED
        redemption.save(update_fields=["match_status", "updated_at"])
        raise ValidationError({"offer_code": "Offer is no longer active."})

    redemption.match_status = Redemption.MatchStatus.MATCHED
    redemption.save(update_fields=["match_status", "updated_at"])
    return redemption


def _assert_merchant_owns(user, redemption):
    if user.role == "super_admin":
        return
    if getattr(user, "merchant_profile", None) != redemption.merchant:
        raise PermissionDenied("This redemption belongs to another merchant.")


def approve_redemption(user, redemption):
    """Story MER-5 (RD 2.7) + CON-3 — finalise and apply points/discount."""
    _assert_merchant_owns(user, redemption)
    if redemption.match_status != Redemption.MatchStatus.MATCHED:
        raise ValidationError("Redemption must be matched before it can be approved.")
    if redemption.approval_status != Redemption.ApprovalStatus.PENDING:
        raise ValidationError(
            f"Redemption is already {redemption.approval_status}."
        )

    with transaction.atomic():
        redemption.approval_status = Redemption.ApprovalStatus.APPROVED
        redemption.approved_by = user
        redemption.approved_at = timezone.now()
        redemption.save(
            update_fields=["approval_status", "approved_by", "approved_at", "updated_at"]
        )

        offer = redemption.offer
        offer.status = Offer.Status.REDEEMED
        offer.save(update_fields=["status", "updated_at"])

        mlp, _ = MerchantLoyaltyPoints.objects.get_or_create(
            consumer=redemption.consumer, merchant=redemption.merchant
        )
        MerchantLoyaltyPoints.objects.filter(pk=mlp.pk).update(
            points_balance=F("points_balance") + MERCHANT_POINTS_ON_REDEEM
        )
        Consumer.objects.filter(pk=redemption.consumer_id).update(
            adme_points_balance=F("adme_points_balance") + ADME_POINTS_ON_REDEEM
        )
        Merchant.objects.filter(pk=redemption.merchant_id).update(
            total_redemptions=F("total_redemptions") + 1
        )
        cm, _ = CampaignMetric.objects.get_or_create(
            campaign=offer.campaign, date=timezone.localdate()
        )
        CampaignMetric.objects.filter(pk=cm.pk).update(
            offers_redeemed=F("offers_redeemed") + 1
        )

    redemption.refresh_from_db()
    return redemption


def reject_redemption(user, redemption, reason=""):
    _assert_merchant_owns(user, redemption)
    if redemption.approval_status != Redemption.ApprovalStatus.PENDING:
        raise ValidationError(f"Redemption is already {redemption.approval_status}.")
    redemption.approval_status = Redemption.ApprovalStatus.REJECTED
    redemption.approved_by = user
    redemption.approved_at = timezone.now()
    redemption.save(
        update_fields=["approval_status", "approved_by", "approved_at", "updated_at"]
    )
    return redemption


def consumer_profile(consumer):
    """Story CON-4 — points balances + redemption history."""
    redemptions = list(
        Redemption.objects.filter(consumer=consumer)
        .select_related("offer", "merchant")
        .order_by("-created_at")[:50]
    )
    merchant_points = (
        MerchantLoyaltyPoints.objects.filter(consumer=consumer)
        .select_related("merchant")
        .order_by("-points_balance")
    )
    base = Redemption.objects.filter(consumer=consumer)
    return {
        "consumer_id": consumer.id,
        "adme_points_balance": consumer.adme_points_balance,
        "merchant_points": [
            {"merchant": mp.merchant.business_name, "points": mp.points_balance}
            for mp in merchant_points
        ],
        "totals": {
            "redemptions_total": base.count(),
            "redemptions_approved": base.filter(
                approval_status=Redemption.ApprovalStatus.APPROVED
            ).count(),
        },
        "redemptions": [redemption_summary(r) for r in redemptions],
    }
