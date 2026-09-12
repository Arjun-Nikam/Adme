from django.conf import settings
from django.db import models
from common.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    """Every create/update/delete/approve across the platform — RD Section 6,
    Story SUP-1/SUP-2. Written via common.audit.AuditLogMixin (or
    self.write_audit(...) for custom actions), never ad hoc per view."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions",
    )
    action = models.CharField(max_length=50)  # create / update / delete / approve
    entity = models.CharField(max_length=100)  # e.g. "Merchant", "Redemption"
    entity_id = models.CharField(max_length=50)
    details = models.JSONField(blank=True, null=True)


class AdMedia(TimeStampedModel):
    class MediaType(models.TextChoices):
        PHOTO = "photo", "Photo"
        VIDEO = "video", "Video"

    title = models.CharField(max_length=150)
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file = models.FileField(upload_to="ad-media/%Y/%m/")
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ad_media",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_ad_media",
    )

    class Meta:
        ordering = ["-created_at"]
