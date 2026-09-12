"""
B6 / Definition of Done: "Action is traceable in audit_logs if it
creates/updates/deletes/approves data."

`AuditLogMixin` is the single, shared mechanism. Add it to any DRF ViewSet
whose writes must be audited:

    class MerchantViewSet(AuditLogMixin, viewsets.ModelViewSet):
        ...

For non-CRUD actions (e.g. an `approve` @action), call `self.write_audit(...)`
directly. Do NOT sprinkle ad-hoc AuditLog.objects.create() calls around views.
"""
from apps.admin_ops.models import AuditLog


class AuditLogMixin:
    #: override on the view if the model name differs from the queryset model
    audit_entity = None

    def _entity_name(self, instance=None):
        if self.audit_entity:
            return self.audit_entity
        if instance is not None:
            return instance.__class__.__name__
        model = getattr(getattr(self, "queryset", None), "model", None)
        return model.__name__ if model else "Unknown"

    def write_audit(self, action, instance, details=None):
        actor = getattr(self.request, "user", None)
        AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            entity=self._entity_name(instance),
            entity_id=str(getattr(instance, "pk", "")),
            details=details or None,
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.write_audit("create", instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.write_audit("update", instance)

    def perform_destroy(self, instance):
        entity, entity_id = self._entity_name(instance), str(instance.pk)
        instance.delete()
        AuditLog.objects.create(
            actor=(
                self.request.user
                if getattr(self.request.user, "is_authenticated", False)
                else None
            ),
            action="delete",
            entity=entity,
            entity_id=entity_id,
        )
