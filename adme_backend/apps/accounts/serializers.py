from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class CustomerSignupRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if get_user_model().objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value


class CustomerSignupVerifySerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()
    code = serializers.CharField(min_length=6, max_length=6)


class UserSerializer(serializers.ModelSerializer):
    """Story CORE-2 — Super Admin user administration."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "role", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class MeSerializer(serializers.ModelSerializer):
    """Payload for GET /api/v1/auth/me/ — client bootstrap after login.

    Carries the linked profile id for the role so each dashboard can fetch its
    own data without a lookup (merchant_id -> merchant dashboard, etc.).
    """

    name = serializers.SerializerMethodField()
    merchant_id = serializers.SerializerMethodField()
    consumer_id = serializers.SerializerMethodField()
    driver_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "email",
            "phone",
            "role",
            "is_active",
            "merchant_id",
            "consumer_id",
            "driver_id",
        ]

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_merchant_id(self, obj):
        return getattr(getattr(obj, "merchant_profile", None), "id", None)

    def get_consumer_id(self, obj):
        return getattr(getattr(obj, "consumer_profile", None), "id", None)

    def get_driver_id(self, obj):
        return getattr(getattr(obj, "driver_profile", None), "id", None)


class AdmeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    CORE-1: put the user's `role` (plus id/name) into the JWT so the Expo
    client can redirect to the correct role screen without a second call,
    and echo them in the login response body.

    `username_field` still drives auth; the custom auth backend
    (apps.accounts.auth.EmailOrPhoneBackend) lets that value be an email or
    a phone number as well (RD CORE-1: "email/phone + password").
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.get_full_name() or user.username
        token["user_id"] = user.id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["name"] = self.user.get_full_name() or self.user.username
        data["user_id"] = self.user.id
        return data
