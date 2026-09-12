import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from common.audit import AuditLogMixin
from common.permissions import IsSuperAdmin

from .models import CustomerSignupChallenge, User
from .serializers import (
    AdmeTokenObtainPairSerializer,
    CustomerSignupRequestSerializer,
    CustomerSignupVerifySerializer,
    MeSerializer,
    UserSerializer,
)


def _customer_login_payload(user):
    token = AdmeTokenObtainPairSerializer.get_token(user)
    return {
        "refresh": str(token),
        "access": str(token.access_token),
        "role": user.role,
        "name": user.get_full_name() or user.username,
        "user_id": user.id,
    }


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def customer_signup_request(request):
    serializer = CustomerSignupRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = timezone.now()
    CustomerSignupChallenge.objects.filter(
        email=data["email"], verified_at__isnull=True
    ).delete()
    challenge = CustomerSignupChallenge.objects.create(
        email=data["email"], phone=data.get("phone", ""),
        first_name=data["first_name"], last_name=data.get("last_name", ""),
        password_hash=make_password(data["password"]), code_hash=make_password(code),
        expires_at=now + timedelta(minutes=10),
    )
    send_mail(
        "Your NearMe verification code",
        f"Your NearMe verification code is {code}. It expires in 10 minutes.",
        None, [challenge.email], fail_silently=False,
    )
    return Response({
        "challenge_id": str(challenge.id),
        "delivery": f"We sent a verification code to {challenge.email}",
        "expires_in_seconds": 600,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def customer_signup_verify(request):
    serializer = CustomerSignupVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        challenge = CustomerSignupChallenge.objects.get(pk=data["challenge_id"])
    except CustomerSignupChallenge.DoesNotExist:
        raise ValidationError("This verification session is no longer valid.")
    if challenge.verified_at or challenge.expires_at <= timezone.now():
        raise ValidationError("This verification code has expired. Start again.")
    if challenge.attempts >= 5:
        raise ValidationError("Too many incorrect attempts. Start again.")
    if not check_password(data["code"], challenge.code_hash):
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])
        raise ValidationError("That verification code is incorrect.")
    with transaction.atomic():
        if User.objects.filter(email__iexact=challenge.email).exists():
            raise ValidationError("An account with this email already exists.")
        user = User.objects.create(
            username=challenge.email, email=challenge.email, phone=challenge.phone,
            first_name=challenge.first_name, last_name=challenge.last_name,
            password=challenge.password_hash, role=User.Role.CONSUMER, is_active=True,
        )
        from apps.consumers.models import Consumer
        Consumer.objects.create(user=user)
        challenge.verified_at = timezone.now()
        challenge.save(update_fields=["verified_at"])
    return Response(_customer_login_payload(user), status=status.HTTP_201_CREATED)


class AdmeTokenObtainPairView(TokenObtainPairView):
    """CORE-1 — login endpoint; returns access + refresh + role."""

    serializer_class = AdmeTokenObtainPairSerializer
    throttle_scope = "login"


class MeView(RetrieveAPIView):
    """GET /api/v1/auth/me/ — the logged-in user, used by the client on boot."""

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    Story CORE-2: Super Admin can list/search/create/deactivate any user and
    assign their role. Every write is recorded in AuditLog by AuditLogMixin.

    CORE-2 acceptance ("deactivating a user immediately blocks further
    logins/API calls"): on is_active -> False we blacklist the user's
    outstanding refresh tokens so they cannot mint new access tokens; the
    current access token then dies at its (short) expiry.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "phone"]

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        was_role = serializer.instance.role
        user = serializer.save()
        details = {}
        if was_role != user.role:
            details["role_change"] = {"from": was_role, "to": user.role}
        if was_active and not user.is_active:
            details["deactivated"] = True
            self._revoke_tokens(user)
        self.write_audit("update", user, details or None)

    def _revoke_tokens(self, user):
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

            for token in OutstandingToken.objects.filter(user=user):
                try:
                    RefreshToken(token.token).blacklist()
                except Exception:
                    pass
        except Exception:
            # token_blacklist not installed / migrated yet — access tokens
            # still expire on their own short lifetime.
            pass
