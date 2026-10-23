from django.apps import AppConfig, apps
from django.conf import settings

from auditlog.registry import register
from auditlog.utils import is_audit_log_enabled


class AuditlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditlog"

    def ready(self):
        # Opt-in master switch
        if not is_audit_log_enabled():
            return

        middleware_to_add = "auditlog.middleware.CurrentUserMiddleware"
        if middleware_to_add not in settings.MIDDLEWARE:
            if isinstance(settings.MIDDLEWARE, tuple):
                settings.MIDDLEWARE = list(settings.MIDDLEWARE)
            try:
                index = settings.MIDDLEWARE.index(
                    "django.contrib.auth.middleware.AuthenticationMiddleware"
                )
                settings.MIDDLEWARE.insert(index + 1, middleware_to_add)
            except ValueError:
                settings.MIDDLEWARE.append(middleware_to_add)

        import auditlog.signals  # noqa

        # Auto-register models from configured apps
        for app_label in getattr(settings, "AUDITLOG_AUTO_REGISTER_APPS", []):
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                continue
            for model in app_config.get_models():
                register(model)
