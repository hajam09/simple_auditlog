from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from auditlog.models import SimpleAuditRecord
from auditlog.utils import get_current_user, is_bulk_audit_enabled


class SimpleAuditRecordBulkQuerySet(models.QuerySet):
    def update(self, **kwargs):
        old_objs = list(self.values("id", *kwargs.keys()))
        result = super().update(**kwargs)

        if not is_bulk_audit_enabled():
            return result

        if not old_objs:
            return result

        user = get_current_user()
        content_type = ContentType.objects.get_for_model(self.model)
        audit_records = []

        for old in old_objs:
            changes = {}
            for field, new_value in kwargs.items():
                old_value = old[field]
                changes[field] = {"old": old_value, "new": new_value, "changed": old_value != new_value}

            if any(d["changed"] for d in changes.values()):
                audit_records.append(
                    SimpleAuditRecord(
                        content_type=content_type,
                        object_id=str(old["id"]),
                        action="updated",
                        changes=changes,
                        changed_by=user,
                    )
                )

        if audit_records:
            with transaction.atomic():
                SimpleAuditRecord.objects.bulk_create(audit_records)

        return result
