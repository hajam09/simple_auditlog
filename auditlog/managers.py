from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from auditlog.models import SimpleAuditRecord
from auditlog.querysets import SimpleAuditRecordBulkQuerySet
from auditlog.utils import get_current_user, json_safe, is_bulk_audit_enabled


class SimpleAuditRecordBulkManager(models.Manager):

    def get_queryset(self):
        return SimpleAuditRecordBulkQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        created_objs = super().bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts)

        if not created_objs or not is_bulk_audit_enabled():
            return created_objs

        user = get_current_user()
        content_type = ContentType.objects.get_for_model(self.model)
        audit_records = []

        for obj in created_objs:
            changes = {
                f.name: {"old": None, "new": json_safe(getattr(obj, f.name)), "changed": True}
                for f in obj._meta.fields
                if f.name != "id"
            }
            audit_records.append(
                SimpleAuditRecord(
                    content_type=content_type,
                    object_id=str(obj.pk),
                    action="created",
                    changes=changes,
                    changed_by=user,
                )
            )

        if audit_records:
            with transaction.atomic():
                SimpleAuditRecord.objects.bulk_create(audit_records)

        return created_objs

    def private_bulk_update(self, objs, fields, batch_size=None):
        """
        IMPORTANT:
            We intentionally do NOT audit QuerySet.update() here.

            Django implements bulk_update() by calling update() with CASE expressions.
            At that level, the ORM no longer knows the per-row "new value" — only a
            SQL expression exists. Auditing update() would therefore:
              - lose per-object value information
              - duplicate bulk_update audit entries
              - attempt to serialize ORM expressions (Case), which fails

            For correctness, bulk_update auditing is handled explicitly in
            SimpleAuditRecordBulkManager.bulk_update().

            QuerySet.update() auditing may be added in the future for literal updates
            (non-expression values) only.
        """
        result = super().bulk_update(objs, fields, batch_size=batch_size)

        if not is_bulk_audit_enabled():
            return result

        # Fetch old values
        old_objs_data = {
            obj.pk: {f: getattr(obj.__class__.objects.get(pk=obj.pk), f) for f in fields}
            for obj in objs
        }

        user = get_current_user()
        content_type = ContentType.objects.get_for_model(self.model)
        audit_records = []

        for obj in objs:
            changes = {}
            old_data = old_objs_data.get(obj.pk, {})
            for field in fields:
                old_value = old_data.get(field)
                new_value = getattr(obj, field)
                changes[field] = {"old": old_value, "new": new_value, "changed": old_value != new_value}

            if any(d["changed"] for d in changes.values()):
                audit_records.append(
                    SimpleAuditRecord(
                        content_type=content_type,
                        object_id=str(obj.pk),
                        action="updated",
                        changes=changes,
                        changed_by=user,
                    )
                )

        if audit_records:
            with transaction.atomic():
                SimpleAuditRecord.objects.bulk_create(audit_records)

        return result

    def update(self, **kwargs):
        """
        Overrides QuerySet.update() to log audit records.
        """
        # Only works if called via `Model.objects.filter(...).update(...)`
        queryset = self.get_queryset()
        user = get_current_user()
        content_type = ContentType.objects.get_for_model(self.model)

        # Fetch old values
        old_objs = list(queryset.values("id", *kwargs.keys()))

        result = super().update(**kwargs)

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
