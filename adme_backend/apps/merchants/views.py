from datetime import date, timedelta
from django.db import transaction

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.analytics import services
from common.audit import AuditLogMixin
from .geo import ALLOWED_RADII_KM, nearby_offers
from common.permissions import (
    CampaignAccess,
    IsRole,
    IsSuperAdmin,
    IsSuperAdminOrReadOnlyAdmin,
    ReadOnly,
)

from .models import (
    AreaMapping,
    Campaign,
    CampaignMetric,
    Category,
    Merchant,
    Offer,
    Plan,
    Report,
)
from .serializers import (
    AreaMappingSerializer,
    CampaignMetricSerializer,
    CampaignSerializer,
    CategorySerializer,
    MerchantSerializer,
    OfferSerializer,
    PlanSerializer,
    ReportSerializer,
    CampaignLaunchSerializer,
    MerchantApplicationSerializer,
)


def _parse_date(value):
    """YYYY-MM-DD string -> date, or None if absent/invalid."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class CategoryViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """RD 2.8 — write = Ops/Super Admin; read = any authenticated user."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        (ReadOnly | IsSuperAdmin),
    ]


class PlanViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """RD 2.9 — Story MER-6. Read for any authed user (needed for signup UI)."""

    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        (ReadOnly | IsSuperAdmin),
    ]


class MerchantViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """RD 2.4 — Story MER-1 (onboarding done by Ops/Super Admin)."""

    queryset = Merchant.objects.select_related("category", "plan").all()
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrReadOnlyAdmin]
    filterset_fields = ["category", "plan", "renewal_status"]
    search_fields = ["business_name", "contact_person", "store_address"]

    @action(detail=False, methods=["post"], url_path="apply", permission_classes=[permissions.AllowAny])
    def apply(self, request):
        serializer = MerchantApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            from apps.accounts.models import User

            user = User.objects.create_user(
                username=data["username"],
                email=data.get("email", ""),
                password=data["password"],
                role=User.Role.MERCHANT,
                phone=data.get("phone", ""),
                is_active=False,
            )
            merchant = Merchant.objects.create(user=user, **{
                key: data[key]
                for key in (
                    "business_name", "contact_person", "store_address", "latitude",
                    "longitude", "category", "plan", "contract_expiry_date",
                )
                if key in data
            })
            merchant.approval_status = Merchant.ApprovalStatus.PENDING
            merchant.save(update_fields=["approval_status", "updated_at"])
        self.write_audit("create", merchant)
        return Response({
            "merchant_id": merchant.id,
            "approval_status": merchant.approval_status,
            "message": "Application submitted. Adme will review your details before activation.",
        }, status=201)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[
            permissions.IsAuthenticated,
            IsRole.for_roles("merchant", "admin", "super_admin"),
        ],
    )
    def dashboard(self, request, pk=None):
        """
        A `merchant` may only see their own dashboard; `admin`/`super_admin`
        may see any. Optional `?start=YYYY-MM-DD&end=YYYY-MM-DD` (default: last
        30 days).
        """
        merchant = self.get_object()
        if request.user.role == "merchant":
            own = getattr(request.user, "merchant_profile", None)
            if own is None or own.pk != merchant.pk:
                raise PermissionDenied("You can only view your own dashboard.")

        end = _parse_date(request.query_params.get("end")) or date.today()
        start = _parse_date(request.query_params.get("start")) or (
            end - timedelta(days=30)
        )
        return Response(services.merchant_dashboard(merchant, start, end))


class AreaMappingViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """RD 2.10 — Story MER-6."""

    queryset = AreaMapping.objects.all()
    serializer_class = AreaMappingSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrReadOnlyAdmin]


class CampaignViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Campaign.objects.select_related("merchant").all()
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated, CampaignAccess]
    filterset_fields = ["merchant", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.user.role
        if role == "merchant":
            return qs.filter(merchant__user=self.request.user)
        if role == "consumer":
            today = date.today()
            return qs.filter(status=Campaign.Status.ACTIVE, start_date__lte=today, end_date__gte=today)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == "merchant":
            merchant = getattr(self.request.user, "merchant_profile", None)
            if merchant is None:
                raise ValidationError("This account has no merchant profile.")
            if merchant.approval_status != Merchant.ApprovalStatus.APPROVED:
                raise PermissionDenied("Your merchant application must be approved before publishing ads.")
            serializer.save(merchant=merchant)
            return
        serializer.save()

    @action(
        detail=False,
        methods=["post"],
        url_path="launch",
        permission_classes=[permissions.IsAuthenticated, IsRole.for_roles("merchant")],
    )
    def launch(self, request):
        serializer = CampaignLaunchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = getattr(request.user, "merchant_profile", None)
        if merchant is None:
            raise ValidationError("This account has no merchant profile.")
        if merchant.approval_status != Merchant.ApprovalStatus.APPROVED:
            raise PermissionDenied("Your merchant application must be approved before publishing ads.")
        data = serializer.validated_data
        with transaction.atomic():
            campaign = Campaign.objects.create(
                merchant=merchant,
                title=data["title"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                status=Campaign.Status.ACTIVE,
            )
            offer = Offer.objects.create(
                merchant=merchant,
                campaign=campaign,
                offer_code=data["offer_code"],
                title=data["offer_title"],
                description=data.get("description", ""),
                discount_value=data["discount_value"],
            )
        self.write_audit("create", campaign)
        return Response({
            "campaign": CampaignSerializer(campaign).data,
            "offer": OfferSerializer(offer).data,
        }, status=201)

    @action(
        detail=False,
        methods=["get"],
        url_path="live",
        permission_classes=[permissions.IsAuthenticated, IsRole.for_roles("consumer", "super_admin")],
    )
    def live(self, request):
        rows = self.get_queryset().filter(
            merchant__approval_status=Merchant.ApprovalStatus.APPROVED
        ).select_related("merchant").prefetch_related("offers")
        return Response([
            {
                "id": campaign.id,
                "title": campaign.title,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "merchant": campaign.merchant.business_name,
                "offers": OfferSerializer(campaign.offers.filter(status=Offer.Status.ACTIVE), many=True).data,
            }
            for campaign in rows.order_by("end_date", "-created_at")
        ])


class OfferViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """RD 2.6/2.7 — offers. Number matching + approval is the redemption flow
    and lives on apps.consumers.RedemptionViewSet (/match/, /{id}/approve/)."""

    queryset = Offer.objects.select_related("merchant", "campaign").all()
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated, CampaignAccess]
    filterset_fields = ["merchant", "campaign", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.user.role
        if role == "merchant":
            return qs.filter(merchant__user=self.request.user)
        if role == "consumer":
            today = date.today()
            return qs.filter(
                status=Offer.Status.ACTIVE,
                campaign__status=Campaign.Status.ACTIVE,
                merchant__approval_status=Merchant.ApprovalStatus.APPROVED,
                campaign__start_date__lte=today,
                campaign__end_date__gte=today,
            )
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == "merchant":
            merchant = getattr(self.request.user, "merchant_profile", None)
            if merchant is None:
                raise ValidationError("This account has no merchant profile.")
            if merchant.approval_status != Merchant.ApprovalStatus.APPROVED:
                raise PermissionDenied("Your merchant application must be approved before publishing ads.")
            if serializer.validated_data["campaign"].merchant_id != merchant.id:
                raise ValidationError("The campaign must belong to your merchant account.")
            serializer.save(merchant=merchant)
            return
        serializer.save()

    def perform_update(self, serializer):
        if self.request.user.role == "merchant":
            merchant = getattr(self.request.user, "merchant_profile", None)
            if merchant is None:
                raise ValidationError("This account has no merchant profile.")
            campaign = serializer.validated_data.get("campaign", serializer.instance.campaign)
            if campaign.merchant_id != merchant.id:
                raise ValidationError("The campaign must belong to your merchant account.")
            serializer.save(merchant=merchant)
            return
        serializer.save()

    @action(
        detail=False,
        methods=["get"],
        url_path="near-me",
        permission_classes=[
            permissions.IsAuthenticated,
            IsRole.for_roles("consumer", "super_admin"),
        ],
    )
    def near_me(self, request):
        """
        Story CON-2 (RD 3) — active offers within `radius_km` of `lat`,`lng`,
        nearest first. radius_km must be one of 0.5 / 1 / 3.
        """
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, ValueError):
            raise ValidationError({"detail": "lat and lng query params are required."})

        raw_radius = request.query_params.get("radius_km", "1")
        try:
            radius = float(raw_radius)
        except ValueError:
            raise ValidationError({"radius_km": "Must be a number."})
        if radius not in ALLOWED_RADII_KM:
            raise ValidationError(
                {"radius_km": f"Choose one of {list(ALLOWED_RADII_KM)}."}
            )

        return Response(nearby_offers(lat, lng, radius))


class CampaignMetricViewSet(viewsets.ModelViewSet):
    """Daily rollup rows (RD 2.2). Written by Celery, not humans — `admin`
    must not be able to edit the numbers (RD Section 4)."""

    queryset = CampaignMetric.objects.all()
    serializer_class = CampaignMetricSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdminOrReadOnlyAdmin]
    filterset_fields = ["campaign", "date"]


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """RD 2.1 — Story MER-2. Reports are generated by apps.reports (Celery),
    this endpoint just lists/serves them to the merchant."""

    queryset = Report.objects.select_related("merchant").all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["merchant"]
