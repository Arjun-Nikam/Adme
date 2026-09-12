"""
Role-based permission classes shared across every app.

Every DRF view MUST declare permission_classes explicitly — do not rely on
the global default alone once a view needs role restriction.

Role -> access matrix (see docs/architecture.md for the authoritative table):

    super_admin  full CRUD everywhere
    admin        read-only, platform-wide (RD Section 4)
    merchant     own merchant data (RD Section 2)
    consumer     own consumer data (RD Section 3)
    driver       own driver/KYC data + GPS ingest (RD Section 5)
    hardware     GPS + heartbeat ingest only (RD Section 5), device-auth
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsRole(BasePermission):
    """Usage: permission_classes = [IsRole.for_roles("merchant", "super_admin")]"""

    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in self.allowed_roles
        )

    @classmethod
    def for_roles(cls, *roles):
        return type("IsRoleDynamic", (cls,), {"allowed_roles": roles})


class IsSuperAdmin(IsRole):
    allowed_roles = ("super_admin",)


class IsAdminOrSuperAdmin(IsRole):
    allowed_roles = ("admin", "super_admin")


class IsMerchant(IsRole):
    allowed_roles = ("merchant",)


class IsConsumer(IsRole):
    allowed_roles = ("consumer",)


class ReadOnly(BasePermission):
    """Grants only safe methods. Combine with a role class, don't use alone."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsSuperAdminOrReadOnlyAdmin(BasePermission):
    """
    RD Section 4 enforcement: `admin` is strictly read-only, `super_admin`
    has full CRUD. Use on every ViewSet an `admin` can reach that also
    exposes write methods (e.g. CampaignMetric, AreaMapping, Plan admin).
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        role = getattr(user, "role", None)
        if role == "super_admin":
            return True
        if role == "admin":
            return request.method in SAFE_METHODS
        return False


class CampaignAccess(BasePermission):
    """Consumers read live ads; merchants manage only their own campaigns."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        role = getattr(user, "role", None)
        if role == "super_admin":
            return True
        if role == "admin":
            return request.method in SAFE_METHODS
        return role in ("merchant", "consumer") and request.method in SAFE_METHODS or (
            role == "merchant" and request.method not in SAFE_METHODS
        )
