from rest_framework import serializers

from .models import Consumer, MerchantLoyaltyPoints, Redemption


class ConsumerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Consumer
        fields = [
            "id", "user", "username", "name", "email", "phone",
            "adme_points_balance", "created_at", "updated_at",
        ]
        read_only_fields = ["user", "adme_points_balance", "created_at", "updated_at"]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class MerchantLoyaltyPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantLoyaltyPoints
        fields = "__all__"


class RedemptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redemption
        fields = "__all__"
        read_only_fields = [
            "match_status",
            "approval_status",
            "approved_by",
            "approved_at",
            "merchant",
        ]


class ScanInputSerializer(serializers.Serializer):
    """Story CON-1 — scan a QR / type an offer number."""

    offer_code = serializers.CharField(max_length=50)
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )


class MatchInputSerializer(serializers.Serializer):
    """Story MER-5 — merchant enters the consumer's offer code."""

    offer_code = serializers.CharField(max_length=50)


class RejectInputSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class RedemptionSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    offer_code = serializers.CharField()
    offer_title = serializers.CharField()
    merchant = serializers.CharField()
    discount_value = serializers.FloatField()
    match_status = serializers.CharField()
    approval_status = serializers.CharField()
    store_visit_confirmed = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    approved_at = serializers.DateTimeField(allow_null=True)
