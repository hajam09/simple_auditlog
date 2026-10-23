import sys

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import m2m_changed
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from auditlog.models import SimpleAuditRecord
from auditlog.registry import is_registered
from auditlog.utils import get_current_user, is_m2m_audit_enabled, serialize_instance, json_safe

# --------------------------------------
# Configuration
# --------------------------------------

DEFAULT_IGNORED_APPS = {
    "admin",
    "sessions",
    "contenttypes",
    "auditlog",
}

IGNORED_APPS = set(
    getattr(settings, "AUDITLOG_IGNORED_APPS", DEFAULT_IGNORED_APPS)
)


def is_running_migrations():
    return "makemigrations" in sys.argv or "migrate" in sys.argv


# --------------------------------------
# Signal handlers
# --------------------------------------

def should_audit(sender):
    if sender._meta.app_label in IGNORED_APPS:
        return False
    return is_registered(sender)


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not should_audit(sender):
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._audit_old_state = serialize_instance(old_instance)
        except sender.DoesNotExist:
            instance._audit_old_state = None
    else:
        instance._audit_old_state = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not should_audit(sender):
        return

    user = get_current_user()
    content_type = ContentType.objects.get_for_model(sender)
    new_state = serialize_instance(instance)

    if created:
        changes = {
            field: {
                "old": None,
                "new": value,
                "changed": True,
            }
            for field, value in new_state.items()
        }
        action = "created"
    else:
        old_state = getattr(instance, "_audit_old_state", {}) or {}
        changes = {}
        for field, new_value in new_state.items():
            old_value = old_state.get(field)
            changes[field] = {
                "old": json_safe(old_value),
                "new": json_safe(new_value),
                "changed": old_value != new_value,
            }

        if not any(v["changed"] for v in changes.values()):
            return
        action = "updated"

    SimpleAuditRecord.objects.create(
        content_type=content_type,
        object_id=str(instance.pk),
        action=action,
        changes=changes,
        changed_by=user,
    )


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    if not should_audit(sender):
        return

    user = get_current_user()
    content_type = ContentType.objects.get_for_model(sender)
    old_state = serialize_instance(instance)

    changes = {
        field: {
            "old": value,
            "new": None,
            "changed": True,
        }
        for field, value in old_state.items()
    }

    SimpleAuditRecord.objects.create(
        content_type=content_type,
        object_id=str(instance.pk),
        action="deleted",
        changes=changes,
        changed_by=user,
    )


if is_m2m_audit_enabled():
    @receiver(m2m_changed)
    def audit_m2m_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
        if action not in {"post_add", "post_remove", "post_clear"}:
            return

        if not should_audit(instance.__class__):
            return

        user = get_current_user()
        content_type = ContentType.objects.get_for_model(instance)

        field_name = sender._meta.model_name

        if action == "post_clear":
            changes = {
                field_name: {
                    "old": "ALL",
                    "new": [],
                    "changed": True,
                }
            }
        else:
            changes = {
                field_name: {
                    "old": [],
                    "new": list(pk_set),
                    "changed": True,
                }
            }

        SimpleAuditRecord.objects.create(
            content_type=content_type,
            object_id=str(instance.pk),
            action="updated",
            changes=changes,
            changed_by=user,
        )
