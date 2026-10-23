import os
from datetime import timedelta, time
from decimal import Decimal

import factory
from django.utils import timezone

from testing.models import RelatedModel, ComprehensiveModel


class RelatedModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RelatedModel

    name = factory.Sequence(lambda n: f"Related {n}")


class ComprehensiveModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ComprehensiveModel

    # Core fields
    char = "char value"
    text = "some long text"
    boolean = True
    integer = -10
    positive_integer = 10
    positive_big_integer = 100000
    positive_small_integer = 5
    big_integer = 9999999999
    small_integer = -5
    float_field = 3.14159
    decimal = Decimal("9.99")

    # Date / time
    date = factory.LazyFunction(lambda: timezone.now().date())
    datetime = factory.LazyFunction(timezone.now)
    time = time(14, 45)
    duration = timedelta(seconds=120)

    # Other
    json = {"key": "value", "nested": {"a": 1}}
    email = "test@example.com"
    url = "https://example.com"
    slug = "test-slug"
    file_path = factory.LazyFunction(lambda: os.getcwd())
    ip_address = "127.0.0.1"
    binary = b"\x00\x01\x02"
    uuid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    # Relations
    foreign_key = None  # factory.SubFactory(RelatedModelFactory, optional=True)
    one_to_one = None  # factory.SubFactory(RelatedModelFactory, optional=True)

    @factory.post_generation
    def many_to_many(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.many_to_many.add(*extracted)
