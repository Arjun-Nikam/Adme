from rest_framework import serializers
from .models import Driver, HardwareUnit, Rickshaw, GpsPing, UptimeLog


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = "__all__"
        read_only_fields = ["kyc_status", "kyc_approved_by"]


class HardwareUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardwareUnit
        fields = "__all__"
        read_only_fields = ["status", "last_heartbeat_at"]


class RickshawSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rickshaw
        fields = "__all__"


class GpsPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GpsPing
        fields = "__all__"


class UptimeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UptimeLog
        fields = "__all__"
