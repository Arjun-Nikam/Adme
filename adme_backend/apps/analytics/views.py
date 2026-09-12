from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrSuperAdmin

from . import services
from django.shortcuts import get_object_or_404

from .serializers import (
    AdvertiserDetailSerializer,
    AdvertiserRowSerializer,
    LiveFleetRowSerializer,
    PlatformOverviewSerializer,
)

ADMIN_READ = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]


class PlatformOverviewView(APIView):
    """Story ADM-1 — headline counters; Admin + Super Admin only (RD Section 4)."""

    permission_classes = ADMIN_READ

    @extend_schema(responses=PlatformOverviewSerializer)
    def get(self, request):
        return Response(services.platform_overview())


class AdvertiserDirectoryView(APIView):
    """Story ADM-1 (RD 4.3) — advertiser directory with campaign status + spend."""

    permission_classes = ADMIN_READ

    @extend_schema(responses=AdvertiserRowSerializer(many=True))
    def get(self, request):
        approval_status = request.query_params.get("approval_status")
        return Response(services.advertiser_directory(approval_status=approval_status))


class AdvertiserDetailView(APIView):
    permission_classes = ADMIN_READ

    @extend_schema(responses=AdvertiserDetailSerializer)
    def get(self, request, pk):
        from apps.merchants.models import Merchant

        merchant = get_object_or_404(Merchant, pk=pk)
        return Response(services.advertiser_detail(merchant.id))


class LiveFleetView(APIView):
    """Story ADM-1 (RD 4.1) — active rickshaws + latest position + live flag."""

    permission_classes = ADMIN_READ

    @extend_schema(responses=LiveFleetRowSerializer(many=True))
    def get(self, request):
        return Response(services.live_fleet())
