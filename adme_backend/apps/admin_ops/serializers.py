from rest_framework import serializers
from .models import AdMedia, AuditLog
from apps.merchants.models import Merchant


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class AdMediaSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    merchant_name = serializers.CharField(source="merchant.business_name", read_only=True)

    class Meta:
        model = AdMedia
        fields = [
            "id", "title", "media_type", "file", "merchant", "merchant_name",
            "uploaded_by", "created_at",
        ]
        read_only_fields = ["id", "merchant_name", "uploaded_by", "created_at"]

    def validate(self, attrs):
        uploaded_file = attrs.get("file")
        media_type = attrs.get("media_type")
        if uploaded_file:
            content_type = uploaded_file.content_type or ""
            if media_type == AdMedia.MediaType.PHOTO and not content_type.startswith("image/"):
                raise serializers.ValidationError({"file": "Photo uploads must be an image."})
            if media_type == AdMedia.MediaType.VIDEO and not content_type.startswith("video/"):
                raise serializers.ValidationError({"file": "Video uploads must be a video."})
            if uploaded_file.size > 100 * 1024 * 1024:
                raise serializers.ValidationError({"file": "Media files must be 100 MB or smaller."})
        return attrs


class MerchantVerificationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Merchant
        fields = [
            "id", "username", "email", "phone", "business_name",
            "contact_person", "store_address", "latitude", "longitude",
            "category", "plan", "contract_expiry_date", "approval_status",
            "created_at",
        ]
        read_only_fields = fields
