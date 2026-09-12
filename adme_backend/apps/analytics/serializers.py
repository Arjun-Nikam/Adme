"""Response shapes for the read-only Admin dashboard (Story ADM-1).

These are plain (non-model) serializers used for API docs / drf-spectacular;
the data comes from apps.analytics.services.
"""
from rest_framework import serializers


class PlatformOverviewSerializer(serializers.Serializer):
    total_live_rickshaws = serializers.IntegerField()
    total_redemptions = serializers.IntegerField()
    advertiser_count = serializers.IntegerField()
    generated_at = serializers.DateTimeField()


class AdvertiserRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_name = serializers.CharField()
    approval_status = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    plan = serializers.CharField(allow_null=True)
    renewal_status = serializers.CharField()
    contract_expiry_date = serializers.DateField(allow_null=True)
    active_campaigns = serializers.IntegerField()
    total_redemptions = serializers.IntegerField()
    spend = serializers.FloatField()


class AdvertiserDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_name = serializers.CharField()
    contact_person = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    store_address = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    approval_status = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    plan = serializers.CharField(allow_null=True)
    contract_expiry_date = serializers.DateField(allow_null=True)
    media = serializers.ListField()
    rickshaws = serializers.ListField()


class LiveFleetRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    registration_number = serializers.CharField()
    driver_name = serializers.CharField(allow_null=True)
    hardware_serial = serializers.CharField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)
    last_ping_at = serializers.DateTimeField(allow_null=True)
    is_live = serializers.BooleanField()
