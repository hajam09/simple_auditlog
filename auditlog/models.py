from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.html import format_html


class SimpleAuditRecord(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    content_object = GenericForeignKey("content_type", "object_id")

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changes = models.JSONField()

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "SimpleAuditRecord"
        verbose_name_plural = "SimpleAuditRecords"

    def admin_object_link(self):
        if not self.content_object:
            return "Object deleted"
        ct = self.content_type
        url_name = f"admin:{ct.app_label}_{ct.model}_change"
        try:
            url = reverse(url_name, args=[self.object_id])
        except NoReverseMatch:
            return "Admin view not available"
        return format_html('<a href="{}">{}</a>', url, str(self.content_object))

    @staticmethod
    def audit_history_link(obj):
        """
        Returns a link to view all audit records for the object
        """
        ct_id = ContentType.objects.get_for_model(obj).id
        url = (
                reverse("admin:auditlog_auditrecord_changelist")
                + f"?content_type__id__exact={ct_id}&object_id__exact={obj.pk}"
        )
        return format_html('<a href="{}">View Audit History</a>', url)

    def __str__(self):
        return (
            f"{self.content_type.app_label}."
            f"{self.content_type.model}({self.object_id}) "
            f"{self.action}"
        )
