from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.audit import AuditLogMixin
from common.permissions import IsRole

from . import services
from .models import Consumer, MerchantLoyaltyPoints, Redemption
from .serializers import (
    ConsumerSerializer,
    MatchInputSerializer,
    MerchantLoyaltyPointsSerializer,
    RedemptionSerializer,
    RedemptionSummarySerializer,
    RejectInputSerializer,
    ScanInputSerializer,
)

IsConsumer = IsRole.for_roles("consumer", "super_admin")
IsMerchantActor = IsRole.for_roles("merchant", "super_admin")


def _my_consumer(request):
    # fetch fresh (avoids a stale cached reverse relation on request.user)
    consumer = Consumer.objects.filter(user=request.user).first()
    if consumer is None:
        raise ValidationError("This account has no consumer profile.")
    return consumer


def _my_merchant(request):
    from apps.merchants.models import Merchant

    merchant = Merchant.objects.filter(user=request.user).first()
    if merchant is None:
        raise ValidationError("This account has no merchant profile.")
    return merchant


class ConsumerViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Consumer.objects.select_related("user").all()
    serializer_class = ConsumerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role in ("admin", "super_admin"):
            return qs
        return qs.filter(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="me",
            permission_classes=[permissions.IsAuthenticated, IsConsumer])
    def me(self, request):
        """Story CON-4 — the signed-in consumer's profile + points + history."""
        return Response(services.consumer_profile(_my_consumer(request)))

    @action(detail=True, methods=["get"], url_path="profile",
            permission_classes=[permissions.IsAuthenticated,
                                IsRole.for_roles("admin", "super_admin")])
    def profile(self, request, pk=None):
        """Same payload as /me/, for Admin/Super Admin oversight (RD 3)."""
        return Response(services.consumer_profile(self.get_object()))


class MerchantLoyaltyPointsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MerchantLoyaltyPoints.objects.select_related("merchant", "consumer")
    serializer_class = MerchantLoyaltyPointsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.user.role
        if role in ("admin", "super_admin"):
            return qs
        if role == "consumer":
            return qs.filter(consumer__user=self.request.user)
        if role == "merchant":
            return qs.filter(merchant__user=self.request.user)
        return qs.none()


class RedemptionViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    RD 2.6 / 2.7 / 3. Consumers create rows via /scan/; merchants /match/ then
    /{id}/approve/ (or /reject/). Everyone is scoped to their own rows.
    """

    queryset = Redemption.objects.select_related("offer", "merchant", "consumer")
    serializer_class = RedemptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["match_status", "approval_status", "merchant", "consumer"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.user.role
        if role in ("admin", "super_admin"):
            return qs
        if role == "consumer":
            return qs.filter(consumer__user=self.request.user)
        if role == "merchant":
            return qs.filter(merchant__user=self.request.user)
        return qs.none()

    def get_permissions(self):
        # Raw CRUD is Super Admin only — everyone else goes through the flow
        # actions (scan / match / approve / reject).
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(),
                    IsRole.for_roles("super_admin")()]
        return super().get_permissions()

    @extend_schema(request=ScanInputSerializer, responses=RedemptionSerializer)
    @action(detail=False, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsConsumer])
    def scan(self, request):
        """Story CON-1 — scan a QR or type an offer number."""
        data = ScanInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        redemption = services.scan_offer(
            _my_consumer(request),
            data.validated_data["offer_code"],
            data.validated_data.get("latitude"),
            data.validated_data.get("longitude"),
        )
        self.write_audit("create", redemption)
        return Response(RedemptionSerializer(redemption).data, status=201)

    @extend_schema(request=MatchInputSerializer, responses=RedemptionSerializer)
    @action(detail=False, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsMerchantActor])
    def match(self, request):
        """Story MER-5 (RD 2.6) — merchant enters the consumer's offer code."""
        data = MatchInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        redemption = services.match_offer(
            _my_merchant(request), data.validated_data["offer_code"]
        )
        self.write_audit("update", redemption, {"match_status": "matched"})
        return Response(RedemptionSerializer(redemption).data)

    @extend_schema(request=None, responses=RedemptionSerializer)
    @action(detail=True, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsMerchantActor])
    def approve(self, request, pk=None):
        """Story MER-5 (RD 2.7) — finalise a matched redemption + apply points."""
        redemption = services.approve_redemption(request.user, self.get_object())
        self.write_audit("approve", redemption, {"approval_status": "approved"})
        return Response(RedemptionSerializer(redemption).data)

    @extend_schema(request=RejectInputSerializer, responses=RedemptionSerializer)
    @action(detail=True, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsMerchantActor])
    def reject(self, request, pk=None):
        data = RejectInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        redemption = services.reject_redemption(
            request.user, self.get_object(), data.validated_data["reason"]
        )
        self.write_audit("update", redemption, {"approval_status": "rejected"})
        return Response(RedemptionSerializer(redemption).data)

    @extend_schema(responses=RedemptionSummarySerializer(many=True))
    @action(detail=False, methods=["get"], url_path="me",
            permission_classes=[permissions.IsAuthenticated, IsConsumer])
    def mine(self, request):
        """The signed-in consumer's redemption history."""
        rows = [
            services.redemption_summary(r)
            for r in self.get_queryset().order_by("-created_at")[:100]
        ]
        return Response(rows)
