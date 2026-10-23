# Simple Audit Log for Django

`simple-auditlog` is a lightweight, explicit, and admin-friendly audit logging app for Django.

It records **create, update, and delete** actions for your models, tracks **who made the change**, stores **field-level
diffs**, and presents everything in a clean, readable **Django Admin interface**.

The design is **opt-in by default** — nothing is audited unless you explicitly enable it and register models.

---

## Features

- Track model **create / update / delete**
- Works with **any Django model**
- Field-level diffs stored as JSON
- Inline before/after diffs in Django Admin
- Tracks user from admin, views, APIs, and shell
- Custom user model support
- Async-safe (ASGI compatible)
- Explicit model registration (no surprise logging)

---

## Requirements

- Python 3.8+
- Django 3.2+

---

## Installation

```bash
pip install simple-auditlog

Add it to INSTALLED_APPS:

INSTALLED_APPS = [
    ...
    "auditlog",
]

python manage.py migrate
```

## Settings Configuration

Enable / Disable Audit Logging. Audit logging is enabled by default.

```
AUDITLOG_ENABLED = True
```

Set to False to completely disable audit logging without uninstalling the app.

## Ignored Apps

By default, the following apps are ignored:

* admin
* sessions
* contenttypes
* auditlog

You can override this list:

```
AUDITLOG_IGNORED_APPS = {
    "admin",
    "sessions",
    "contenttypes",
}
```

Models belonging to ignored apps will never be audited.

## Option 1: Decorator (Recommended for individual models)

Use the decorator only in models.py (or a file imported by models.py).

```
from django.db import models
from auditlog import register


@register
class Order(models.Model):
    number = models.CharField(max_length=50)
    status = models.CharField(max_length=20)


Do not use the decorator in admin.py
```

## Option 2: Register models in AppConfig.ready()

```
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "orders"

    def ready(self):
        from auditlog import register
        from .models import Order, Invoice

        register(Order)
        register(Invoice)

Make sure your app config is used:

INSTALLED_APPS = [
    ...
    "orders.apps.OrdersConfig",
]
```

## Option 3: Auto-register entire apps (Zero boilerplate)

To audit all models in an app, use this setting:

```
AUDITLOG_AUTO_REGISTER_APPS = [
    "orders",
    "billing",
]
```

All models in the listed apps will be audited automatically.

## Minimal Working Example

```
# settings.py

INSTALLED_APPS = [
    ...
    "auditlog",
    "orders",
]

AUDITLOG_ENABLED = True

AUDITLOG_AUTO_REGISTER_APPS = ["orders"]
```

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Audtilog Settings Variables

| Setting                                | Type            | Default                                             | Description                                                                                                                                                                                                                                     |
|----------------------------------------|-----------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`AUDITLOG_ENABLED`**                 | `bool`          | `False`                                             | Master switch. Set to `False` to completely disable audit logging.                                                                                                                                                                              |
| **`AUDITLOG_IGNORED_APPS`**            | `list` or `set` | `["admin", "sessions", "contenttypes", "auditlog"]` | List of app labels to exclude from auditing. Models from these apps will never be tracked.                                                                                                                                                      |
| **`AUDITLOG_AUTO_REGISTER_APPS`**      | `list`          | `[]`                                                | List of app labels whose models should automatically be registered for auditing. Only models from these apps will be tracked.                                                                                                                   |
| **`AUDITLOG_BULK_OPERATIONS_ENABLED`** | `bool`          | `False`                                             | Enable logging for bulk operations such as `bulk_create`, `bulk_update`, and `QuerySet.update()`. If `False`, bulk changes are not logged. Set `objects = SimpleAuditRecordBulkManager()` to each model to utilise auditlog for bulk operations. |
| **`AUDITLOG_LOG_M2M`**                 | `bool`          | `False`                                             | Enable logging for Many-to-Many field changes. If `False`, M2M changes are ignored.                                                                                                                                                             |
