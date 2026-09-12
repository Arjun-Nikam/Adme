from django.conf import settings
from django.db import models
from common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class NotificationType(models.TextChoices):
        PLAN_EXPIRY_ALERT = "plan_expiry_alert", "Plan Expiry Alert"
        REPORT_READY = "report_ready", "Report Ready"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=Channel.choices)
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
