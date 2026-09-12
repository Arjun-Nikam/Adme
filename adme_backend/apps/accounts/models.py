from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Single login table for every role in the Ops Screen Module (RD Section 1).
    The `role` field is what the frontend uses to redirect to the correct
    dashboard after login (see Story CORE-1 in the dev plan).
    """

    class Role(models.TextChoices):
        MERCHANT = "merchant", "Merchant"
        CONSUMER = "consumer", "Consumer"
        ADMIN = "admin", "Admin"
        DRIVER = "driver", "Driver"
        HARDWARE = "hardware", "Hardware"
        SUPER_ADMIN = "super_admin", "Super Admin"

    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class CustomerSignupChallenge(models.Model):
    """One-time email verification challenge for NearMe customers."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    password_hash = models.CharField(max_length=128)
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["email", "created_at"])]
