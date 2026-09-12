"""Auto Rickshaw module — Dev Plan Section 5.4 (RD Section 5)."""
from django.conf import settings
from django.db import models
from common.models import TimeStampedModel


class Driver(TimeStampedModel):
    class KycStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver_profile")
    license_number = models.CharField(max_length=100)
    vehicle_rc_number = models.CharField(max_length=100)
    id_proof_url = models.URLField(blank=True)
    kyc_status = models.CharField(max_length=20, choices=KycStatus.choices, default=KycStatus.PENDING)
    kyc_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="kyc_approvals"
    )

    def __str__(self):
        return f"Driver {self.license_number}"


class HardwareUnit(TimeStampedModel):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    serial_number = models.CharField(max_length=100, unique=True)
    model = models.CharField(max_length=100, blank=True)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OFFLINE)

    def __str__(self):
        return self.serial_number


class Rickshaw(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    registration_number = models.CharField(max_length=50, unique=True)
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rickshaws",
    )
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="rickshaws")
    hardware_unit = models.OneToOneField(
        HardwareUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name="rickshaw"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INACTIVE)

    def __str__(self):
        return self.registration_number


class GpsPing(TimeStampedModel):
    """Live telemetry feed powering the fleet map (Story RIK-2)."""
    rickshaw = models.ForeignKey(Rickshaw, on_delete=models.CASCADE, related_name="gps_pings")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    recorded_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["rickshaw", "-recorded_at"])]


class UptimeLog(TimeStampedModel):
    """Heartbeat rollup used for ad-impression auditing (Story RIK-4)."""
    hardware_unit = models.ForeignKey(HardwareUnit, on_delete=models.CASCADE, related_name="uptime_logs")
    checked_at = models.DateTimeField()
    is_online = models.BooleanField()
