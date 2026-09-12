"""
Shared analytics/aggregation service — the SAME functions power the Merchant
dashboard (single merchant), the Admin overview (platform-wide, read-only), and
Super Admin views (RD 2.3, 4). Do not duplicate this logic in each app; import
from here.

Time-slot buckets and the store-visit rule are defined in
docs/architecture.md §11.
"""
from datetime import timedelta

from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.utils import timezone

#: a rickshaw counts as "live" (RD 4.1) when it is active AND has sent a GPS
#: ping within this window.
LIVE_RICKSHAW_WINDOW = timedelta(minutes=15)

METRIC_FIELDS = (
    "ad_views",
    "qr_scans",
    "offers_saved",
    "store_visits",
    "offers_redeemed",
)

TIME_SLOTS = ("06-12", "12-17", "17-21", "21-06")


def _slot_for_hour(hour: int) -> str:
    if 6 <= hour < 12:
        return "06-12"
    if 12 <= hour < 17:
        return "12-17"
    if 17 <= hour < 21:
        return "17-21"
    return "21-06"


def campaign_time_series(campaign_id, start_date, end_date):
    """Story MER-3 — daily ad_views/qr_scans for one campaign (line chart)."""
    from apps.merchants.models import CampaignMetric

    return list(
        CampaignMetric.objects.filter(
            campaign_id=campaign_id, date__range=(start_date, end_date)
        )
        .order_by("date")
        .values("date", "ad_views", "qr_scans")
    )


def merchant_time_series(merchant_id, start_date, end_date):
    """Story MER-3 — daily metrics summed across all of a merchant's campaigns."""
    from apps.merchants.models import CampaignMetric

    rows = (
        CampaignMetric.objects.filter(
            campaign__merchant_id=merchant_id,
            date__range=(start_date, end_date),
        )
        .values("date")
        .annotate(**{f: Sum(f) for f in METRIC_FIELDS})
        .order_by("date")
    )
    return [
        {"date": r["date"], **{f: r[f] or 0 for f in METRIC_FIELDS}} for r in rows
    ]


def redemption_breakdown(merchant_id=None):
    """
    Story MER-3 — pie/bar chart data as ``[{"label", "value"}]``.

    Single merchant  -> approved redemptions bucketed by time slot.
    Platform-wide    -> approved redemptions bucketed by merchant category.
    """
    from apps.consumers.models import Redemption

    qs = Redemption.objects.filter(
        approval_status="approved", approved_at__isnull=False
    )
    if merchant_id is not None:
        qs = qs.filter(merchant_id=merchant_id)
        counts = {slot: 0 for slot in TIME_SLOTS}
        for approved_at in qs.values_list("approved_at", flat=True):
            counts[_slot_for_hour(timezone.localtime(approved_at).hour)] += 1
        return [{"label": slot, "value": counts[slot]} for slot in TIME_SLOTS]

    rows = (
        qs.values("merchant__category__name")
        .annotate(value=Count("id"))
        .order_by("-value")
    )
    return [
        {"label": r["merchant__category__name"] or "Uncategorised", "value": r["value"]}
        for r in rows
    ]


def merchant_dashboard(merchant, start_date, end_date):
    """Story MER-3 — the full payload behind GET /merchants/{id}/dashboard/."""
    series = merchant_time_series(merchant.id, start_date, end_date)
    totals = {f: sum(row[f] for row in series) for f in METRIC_FIELDS}
    return {
        "merchant": {"id": merchant.id, "business_name": merchant.business_name},
        "period": {"start": start_date, "end": end_date},
        "totals": totals,
        "time_series": series,
        "redemption_breakdown": redemption_breakdown(merchant.id),
    }


def _live_rickshaw_queryset():
    """Active rickshaws whose latest GPS ping is inside LIVE_RICKSHAW_WINDOW."""
    from apps.rickshaws.models import GpsPing, Rickshaw

    latest_ping = (
        GpsPing.objects.filter(rickshaw=OuterRef("pk"))
        .order_by("-recorded_at")
        .values("recorded_at")[:1]
    )
    cutoff = timezone.now() - LIVE_RICKSHAW_WINDOW
    return (
        Rickshaw.objects.filter(status="active")
        .annotate(last_ping_at=Subquery(latest_ping))
        .filter(last_ping_at__gte=cutoff)
    )


def platform_overview():
    """Story ADM-1 — headline counters for the Admin overview (read-only)."""
    from apps.consumers.models import Redemption
    from apps.merchants.models import Merchant

    return {
        "total_live_rickshaws": _live_rickshaw_queryset().count(),
        "total_redemptions": Redemption.objects.filter(
            approval_status="approved"
        ).count(),
        "advertiser_count": Merchant.objects.filter(
            approval_status="approved"
        ).count(),
        "pending_verifications": Merchant.objects.filter(
            approval_status="pending"
        ).count(),
        "generated_at": timezone.now(),
    }


def advertiser_directory(approval_status="approved"):
    """
    Story ADM-1 (RD 4.3) — merchant/advertiser directory with campaign status
    and spend. Read-only oversight list for Admin + Super Admin.
    """
    from apps.merchants.models import Merchant

    qs = Merchant.objects.select_related("category", "plan")
    if approval_status and approval_status != "all":
        qs = qs.filter(approval_status=approval_status)

    rows = (
        qs.annotate(
            active_campaigns=Count(
                "campaigns",
                filter=Q(
                    campaigns__status="active",
                    approval_status="approved",
                ),
                distinct=True,
            ),
        )
        .order_by("business_name")
    )
    out = []
    for m in rows:
        out.append(
            {
                "id": m.id,
                "business_name": m.business_name,
                "approval_status": m.approval_status,
                "category": m.category.name if m.category_id else None,
                "plan": m.plan.name if m.plan_id else None,
                "renewal_status": m.renewal_status,
                "contract_expiry_date": m.contract_expiry_date,
                "active_campaigns": m.active_campaigns,
                "total_redemptions": m.total_redemptions,
                "spend": float(m.plan.price) if m.plan_id else 0.0,
            }
        )
    return out


def advertiser_detail(merchant_id):
    """Admin advertiser record with owned media and assigned rickshaws."""
    from apps.admin_ops.models import AdMedia
    from apps.merchants.models import Merchant
    from apps.rickshaws.models import Rickshaw

    merchant = Merchant.objects.select_related("user", "category", "plan").get(pk=merchant_id)
    media = AdMedia.objects.filter(merchant=merchant).order_by("-created_at")
    rickshaws = Rickshaw.objects.filter(merchant=merchant).select_related(
        "driver__user", "hardware_unit"
    ).order_by("registration_number")
    return {
        "id": merchant.id,
        "business_name": merchant.business_name,
        "contact_person": merchant.contact_person,
        "email": merchant.user.email,
        "phone": merchant.user.phone,
        "store_address": merchant.store_address,
        "latitude": float(merchant.latitude),
        "longitude": float(merchant.longitude),
        "approval_status": merchant.approval_status,
        "category": merchant.category.name if merchant.category_id else None,
        "plan": merchant.plan.name if merchant.plan_id else None,
        "contract_expiry_date": merchant.contract_expiry_date,
        "media": [
            {
                "id": item.id,
                "title": item.title,
                "media_type": item.media_type,
                "file": item.file.url,
                "created_at": item.created_at,
            }
            for item in media
        ],
        "rickshaws": [
            {
                "id": item.id,
                "registration_number": item.registration_number,
                "status": item.status,
                "driver_name": (item.driver.user.get_full_name() or item.driver.user.username) if item.driver_id else None,
                "hardware_serial": item.hardware_unit.serial_number if item.hardware_unit_id else None,
            }
            for item in rickshaws
        ],
    }


def live_fleet():
    """
    Story ADM-1 (RD 4.1) + feeds the RIK-2 map — active rickshaws with their
    latest position and whether they are currently live.
    """
    from apps.rickshaws.models import Rickshaw

    cutoff = timezone.now() - LIVE_RICKSHAW_WINDOW
    out = []
    for r in (
        Rickshaw.objects.filter(status="active")
        .select_related("driver__user", "hardware_unit")
        .order_by("registration_number")
    ):
        ping = r.gps_pings.order_by("-recorded_at").first()
        driver = None
        if r.driver_id:
            u = r.driver.user
            driver = u.get_full_name() or u.username
        out.append(
            {
                "id": r.id,
                "registration_number": r.registration_number,
                "driver_name": driver,
                "hardware_serial": (
                    r.hardware_unit.serial_number if r.hardware_unit_id else None
                ),
                "latitude": float(ping.latitude) if ping else None,
                "longitude": float(ping.longitude) if ping else None,
                "last_ping_at": ping.recorded_at if ping else None,
                "is_live": bool(ping and ping.recorded_at >= cutoff),
            }
        )
    return out
