import difflib
import json

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html, format_html_join

from auditlog.models import SimpleAuditRecord
from auditlog.registry import get_registered_models

BASE_CELL_STYLE = """
    white-space: pre-wrap;
    font-family: inherit;
    font-size: 13px;
    line-height: 1.4;
    padding: 4px 6px;
    margin: 0;
    width: 100%
    box-sizing: border-box;
    overflow-y: auto;
"""


class AuditedModelFilter(admin.SimpleListFilter):
    title = "Audited model"
    parameter_name = "content_type"

    def lookups(self, request, model_admin):
        """
        Only show content types for registered (audited) models.
        """
        models = get_registered_models()

        content_types = ContentType.objects.get_for_models(*models).values()

        return [
            (ct.id, f"{ct.app_label}.{ct.model}")
            for ct in content_types
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type_id=self.value())
        return queryset


@admin.register(SimpleAuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    list_display = (
        "content_type",
        "object_id",
        "admin_object_link",
        "action",
        "changed_by",
        "changed_at",
        "changes_count",
    )

    list_filter = (
        AuditedModelFilter,
        "action",
        "changed_by",
        "changed_at",
    )

    readonly_fields = (
        "content_type",
        "object_id",
        "admin_object_link",
        "action",
        "changed_by",
        "changed_at",
        "diff_table",
    )

    fields = (
        "content_type",
        "object_id",
        "admin_object_link",
        "action",
        "changed_by",
        "changed_at",
        "diff_table",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def inline_diff_after(self, old, new):
        old_lines = (old or "").splitlines()
        new_lines = (new or "").splitlines()
        diff = difflib.ndiff(old_lines, new_lines)
        html_lines = []

        for line in diff:
            if line.startswith("+ "):
                html_lines.append(
                    format_html(
                        '<div style="background:#0e5a00; color:#eaffea; padding:0; margin:0;">+{}</div>',
                        line[2:],
                    )
                )
            elif line.startswith("- "):
                html_lines.append(
                    format_html(
                        '<div style="background:#560000; color:#ffecec; padding:0; margin:0;">-{}</div>',
                        line[2:],
                    )
                )
            elif line.startswith("? "):
                continue
            else:
                html_lines.append(format_html('<div style="padding:0; margin:0;">{}</div>', line[2:]))

        return format_html(
            '<div style="{}">{}</div>', BASE_CELL_STYLE, format_html_join("", "{}", ((line,) for line in html_lines))
        )

    def to_diffable_string(self, value):
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value) if value is not None else ""

    def diff_table(self, obj):
        """
        Display a table of field changes with inline diff for strings and JSON fields.
        """

        rows = []
        for field, data in obj.changes.items():
            old = data.get("old")
            new = data.get("new")
            changed = data.get("changed")

            old_str = self.to_diffable_string(old)
            new_str = self.to_diffable_string(new)

            before_html = format_html('<div style="{}">{}</div>', BASE_CELL_STYLE, old_str)
            after_html = self.inline_diff_after(old_str, new_str) if changed else format_html(
                '<div style="{}">{}</div>',
                BASE_CELL_STYLE, new_str)

            rows.append((field, before_html, after_html))

        rows_html = format_html_join(
            "",
            "<tr>"
            "<td style='font-weight:600; vertical-align:top; width:20%;'>{}</td>"
            "<td style='vertical-align:top; width:40%;'>{}</td>"
            "<td style='vertical-align:top; width:40%;'>{}</td>"
            "</tr>",
            rows,
        )

        return format_html(
            """
            <table style="
                width:100%;
                border-collapse:collapse;
            ">
                <thead>
                    <tr>
                        <th style="width:160px;">Field</th>
                        <th>Before</th>
                        <th>After</th>
                    </tr>
                </thead>
                <tbody>{}</tbody>
            </table>
            """,
            rows_html,
        )

    diff_table.short_description = "Changes"

    def changes_count(self, obj):
        count = sum(
            1
            for data in (obj.changes or {}).values()
            if data.get("changed")
        )
        return f"{count} changes"

    changes_count.short_description = "Changes"
