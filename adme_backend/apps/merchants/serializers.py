from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Plan, Merchant, AreaMapping, Campaign, Offer, CampaignMetric, Report

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = "__all__"
        read_only_fields = ["total_redemptions", "renewal_status", "approval_status"]


class MerchantApplicationSerializer(serializers.Serializer):
    """Merchant-submitted application for Adme membership."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=255)
    contact_person = serializers.CharField(max_length=255)
    store_address = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), required=False, allow_null=True
    )
    contract_expiry_date = serializers.DateField(required=False, allow_null=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

class CampaignLaunchSerializer(serializers.Serializer):
    """Merchant-facing ad setup: campaign and its consumer offer together."""

    title = serializers.CharField(max_length=255)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    offer_code = serializers.CharField(max_length=50)
    offer_title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    discount_value = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "End date must be on or after start date."})
        if Offer.objects.filter(offer_code=attrs["offer_code"]).exists():
            raise serializers.ValidationError({"offer_code": "This offer code is already in use."})
        return attrs


class AreaMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaMapping
        fields = "__all__"


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"


class CampaignMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignMetric
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["file_url", "sent_via_email", "sent_via_whatsapp"]
