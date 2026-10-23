import uuid

from django.db import models

from auditlog.managers import SimpleAuditRecordBulkManager
from auditlog.registry import register


@register
class RelatedModel(models.Model):
    name = models.CharField(max_length=100)

    objects = SimpleAuditRecordBulkManager()

    def __str__(self):
        return self.name


@register
class ComprehensiveModel(models.Model):
    # Core fields
    char = models.CharField(max_length=255)
    text = models.TextField()
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField()
    positive_integer = models.PositiveIntegerField()
    positive_big_integer = models.PositiveBigIntegerField()
    positive_small_integer = models.PositiveSmallIntegerField()
    big_integer = models.BigIntegerField()
    small_integer = models.SmallIntegerField()
    float_field = models.FloatField()
    decimal = models.DecimalField(max_digits=10, decimal_places=2)

    # Date / time
    date = models.DateField()
    datetime = models.DateTimeField()
    time = models.TimeField()
    duration = models.DurationField()

    # Other
    uuid = models.UUIDField(default=uuid.uuid4)
    json = models.JSONField()
    email = models.EmailField()
    url = models.URLField()
    slug = models.SlugField()
    file_path = models.FilePathField()
    ip_address = models.GenericIPAddressField()
    binary = models.BinaryField()

    # Relations
    foreign_key = models.ForeignKey(
        RelatedModel, on_delete=models.CASCADE, related_name="fk_models", blank=True, null=True
    )
    one_to_one = models.OneToOneField(
        RelatedModel, on_delete=models.CASCADE, related_name="oto_model", blank=True, null=True
    )
    many_to_many = models.ManyToManyField(RelatedModel, related_name="m2m_models", blank=True, null=True)

    objects = SimpleAuditRecordBulkManager()

    def __str__(self):
        return self.char
