from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsAdminOrSuperAdmin
from common.audit import AuditLogMixin
from apps.merchants.models import Merchant
from .models import AdMedia, AuditLog
from .serializers import AdMediaSerializer, AuditLogSerializer, MerchantVerificationSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """RD Section 4 — Admin gets read-only visibility; Super Admin also read-only
    here (audit logs are append-only, created automatically elsewhere)."""
    queryset = AuditLog.objects.all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    filterset_fields = ["entity", "action", "actor"]


class AdMediaViewSet(viewsets.ModelViewSet):
    """Admin media library for uploaded photo and video assets."""

    queryset = AdMedia.objects.select_related("uploaded_by").all()
    serializer_class = AdMediaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        merchant_id = self.request.query_params.get("merchant")
        if merchant_id:
            queryset = queryset.filter(merchant_id=merchant_id)
        return queryset

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()


class MerchantVerificationViewSet(AuditLogMixin, viewsets.ReadOnlyModelViewSet):
    """Admin review queue for merchant applications."""

    queryset = Merchant.objects.select_related("user", "category", "plan").all()
    serializer_class = MerchantVerificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    filterset_fields = ["approval_status"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        merchant = self.get_object()
        merchant.approval_status = Merchant.ApprovalStatus.APPROVED
        merchant.user.is_active = True
        merchant.user.save(update_fields=["is_active"])
        merchant.save(update_fields=["approval_status", "updated_at"])
        self.write_audit("approve", merchant)
        return Response(MerchantVerificationSerializer(merchant).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        merchant = self.get_object()
        merchant.approval_status = Merchant.ApprovalStatus.REJECTED
        merchant.user.is_active = False
        merchant.user.save(update_fields=["is_active"])
        merchant.save(update_fields=["approval_status", "updated_at"])
        self.write_audit("reject", merchant)
        return Response(MerchantVerificationSerializer(merchant).data)
