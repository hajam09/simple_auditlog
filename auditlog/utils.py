import uuid
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from asgiref.local import Local
from django.conf import settings
from django.db import connection
from django.db.models import ForeignKey, Model

_local = Local()


def set_current_user(user):
    _local.user = user


def get_current_user():
    return getattr(_local, "user", None)


def serialize_instance(instance):
    data = {}
    for field in instance._meta.fields:
        if field.name == "id":
            continue  # skip the id field

        value = getattr(instance, field.name)

        # if it's a foreign key, use the string representation
        if isinstance(field, ForeignKey) and value is not None:
            value = str(value)

        data[field.name] = json_safe(value)

    return data


def json_safe(value):
    if value is None:
        return None
    elif isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif isinstance(value, time):
        return value.isoformat()
    elif isinstance(value, timedelta):
        return value.total_seconds()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, set):
        return list(value)
    elif isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    elif isinstance(value, Model):
        return str(value)
    elif isinstance(value, bytes):
        return str(value)
    return value


def is_audit_log_enabled():
    return getattr(settings, "AUDITLOG_ENABLED", True)


def is_bulk_audit_enabled():
    return getattr(settings, "AUDITLOG_BULK_OPERATIONS_ENABLED", True)


def is_m2m_audit_enabled():
    return getattr(settings, "AUDITLOG_LOG_M2M", True)
