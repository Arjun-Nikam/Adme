"""
Story CON-2 "Near Me". v1 = bounding-box prefilter on merchant lat/lng then a
haversine check in Python (docs/architecture.md §7). Swap to MySQL
ST_Distance_Sphere + a SPATIAL index when merchant volume makes this slow.
"""
import math

EARTH_KM = 6371.0
KM_PER_DEG_LAT = 111.0
ALLOWED_RADII_KM = (0.5, 1.0, 3.0)


def haversine_km(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return EARTH_KM * 2 * math.asin(math.sqrt(a))


def nearby_offers(lat, lng, radius_km):
    """Active offers whose merchant is within `radius_km`, nearest first."""
    from .models import Offer

    lat_pad = radius_km / KM_PER_DEG_LAT
    lng_pad = radius_km / (KM_PER_DEG_LAT * max(math.cos(math.radians(lat)), 0.01))

    qs = (
        Offer.objects.filter(
            status=Offer.Status.ACTIVE,
            merchant__approval_status="approved",
            merchant__latitude__range=(lat - lat_pad, lat + lat_pad),
            merchant__longitude__range=(lng - lng_pad, lng + lng_pad),
        )
        .select_related("merchant", "merchant__category")
    )

    rows = []
    for o in qs:
        d = haversine_km(
            lat, lng, float(o.merchant.latitude), float(o.merchant.longitude)
        )
        if d <= radius_km:
            rows.append(
                {
                    "offer_id": o.id,
                    "offer_code": o.offer_code,
                    "title": o.title,
                    "discount_value": float(o.discount_value),
                    "merchant": o.merchant.business_name,
                    "category": (
                        o.merchant.category.name if o.merchant.category_id else None
                    ),
                    "distance_km": round(d, 2),
                }
            )
    rows.sort(key=lambda r: r["distance_km"])
    return rows
