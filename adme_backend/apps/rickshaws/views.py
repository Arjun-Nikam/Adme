from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.audit import AuditLogMixin
from common.permissions import IsAdminOrSuperAdmin

from .models import Driver, GpsPing, HardwareUnit, Rickshaw, UptimeLog
from .serializers import (
    DriverSerializer,
    GpsPingSerializer,
    HardwareUnitSerializer,
    RickshawSerializer,
    UptimeLogSerializer,
)


class DriverViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """Story RIK-1 — driver submits KYC; Ops/Admin approve or reject."""

    queryset = Driver.objects.select_related("user", "kyc_approved_by")
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["kyc_status"]
    search_fields = ["license_number", "vehicle_rc_number", "user__username"]

    @action(detail=True, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsAdminOrSuperAdmin])
    def approve(self, request, pk=None):
        driver = self.get_object()
        driver.kyc_status = Driver.KycStatus.APPROVED
        driver.kyc_approved_by = request.user
        driver.save(update_fields=["kyc_status", "kyc_approved_by"])
        self.write_audit("approve", driver, {"kyc_status": "approved"})
        return Response(DriverSerializer(driver).data)

    @action(detail=True, methods=["post"],
            permission_classes=[permissions.IsAuthenticated, IsAdminOrSuperAdmin])
    def reject(self, request, pk=None):
        driver = self.get_object()
        driver.kyc_status = Driver.KycStatus.REJECTED
        driver.kyc_approved_by = request.user
        driver.save(update_fields=["kyc_status", "kyc_approved_by"])
        self.write_audit(
            "update", driver,
            {"kyc_status": "rejected", "reason": request.data.get("reason", "")},
        )
        return Response(DriverSerializer(driver).data)


class HardwareUnitViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = HardwareUnit.objects.all()
    serializer_class = HardwareUnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status"]
    search_fields = ["serial_number", "model"]

    def get_throttles(self):
        if self.action == "heartbeat":
            self.throttle_scope = "device_ingest"
        return super().get_throttles()

    @action(detail=True, methods=["post"])
    def heartbeat(self, request, pk=None):
        """Story RIK-4 — hardware pings this periodically.
        TODO: swap to device-key auth (ADR 0003)."""
        unit = self.get_object()
        now = timezone.now()
        unit.last_heartbeat_at = now
        unit.status = HardwareUnit.Status.ONLINE
        unit.save(update_fields=["last_heartbeat_at", "status"])
        UptimeLog.objects.create(hardware_unit=unit, checked_at=now, is_online=True)
        return Response({"status": "ok"})


class RickshawViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """Story RIK-2/RIK-3 — fleet + registration/driver/hardware lookup."""

    queryset = Rickshaw.objects.select_related(
        "driver__user", "hardware_unit"
    ).all()
    serializer_class = RickshawSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "registration_number"]
    search_fields = [
        "registration_number",
        "driver__user__username",
        "hardware_unit__serial_number",
    ]


class GpsPingViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = GpsPing.objects.all()
    serializer_class = GpsPingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "device_ingest"
        return super().get_throttles()


class UptimeLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UptimeLog.objects.select_related("hardware_unit")
    serializer_class = UptimeLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    filterset_fields = ["hardware_unit", "is_online"]
