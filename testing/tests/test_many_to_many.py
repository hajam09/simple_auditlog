from django.contrib.auth.models import User
from django.test import TestCase

from auditlog.models import SimpleAuditRecord
from auditlog.utils import set_current_user
from .factories import ComprehensiveModelFactory, RelatedModelFactory


class ManyToManyAuditTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='sample-user')
        set_current_user(self.user)

    def test_add_single_object_to_m2m_field_after_creation(self):
        obj = ComprehensiveModelFactory()
        related = RelatedModelFactory()
        SimpleAuditRecord.objects.all().delete()

        obj.many_to_many.add(related)
        record = SimpleAuditRecord.objects.get()

        self.assertEqual(record.action, "updated")
        self.assertEqual(
            record.changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [related.pk], 'old': []}
        )

        self.assertEqual(self.user, record.changed_by)

    def test_add_multiple_objects_one_by_one_to_m2m_field_after_creation(self):
        obj = ComprehensiveModelFactory()
        r1 = RelatedModelFactory()
        r2 = RelatedModelFactory()
        SimpleAuditRecord.objects.all().delete()

        obj.many_to_many.add(r1)
        obj.many_to_many.add(r2)
        records = SimpleAuditRecord.objects.all().order_by('changed_at')

        self.assertEqual(2, len(records))
        self.assertEqual(records[0].action, 'updated')
        self.assertEqual(
            records[0].changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r1.pk], 'old': []}
        )

        self.assertEqual(records[1].action, 'updated')
        self.assertEqual(
            records[1].changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r2.pk], 'old': []}
        )

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_add_multiple_objects_together_to_m2m_field_after_creation(self):
        obj = ComprehensiveModelFactory()
        r1 = RelatedModelFactory()
        r2 = RelatedModelFactory()
        SimpleAuditRecord.objects.all().delete()

        obj.many_to_many.add(*[r1, r2])
        records = SimpleAuditRecord.objects.all()

        self.assertEqual(1, len(records))
        self.assertEqual(records[0].action, 'updated')
        self.assertEqual(
            records[0].changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r1.pk, r2.pk], 'old': []}
        )

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_remove_single_object_from_m2m_field_after_creation(self):
        r1 = RelatedModelFactory()
        r2 = RelatedModelFactory()
        obj = ComprehensiveModelFactory(many_to_many=[r1, r2])

        SimpleAuditRecord.objects.all().delete()
        obj.many_to_many.remove(r1)
        record = SimpleAuditRecord.objects.get()

        self.assertEqual(
            record.changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r1.pk], 'old': []}
        )

        self.assertEqual(self.user, record.changed_by)

    def test_remove_multiple_objects_from_m2m_field_after_creation(self):
        r1 = RelatedModelFactory()
        r2 = RelatedModelFactory()
        r3 = RelatedModelFactory()
        obj = ComprehensiveModelFactory(many_to_many=[r1, r2, r3])

        SimpleAuditRecord.objects.all().delete()
        obj.many_to_many.remove(*[r1, r2])
        record = SimpleAuditRecord.objects.get()

        self.assertEqual(
            record.changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r1.pk, r2.pk], 'old': []}
        )

        self.assertEqual(self.user, record.changed_by)

    def test_clear_m2m_field(self):
        obj = ComprehensiveModelFactory(
            many_to_many=[
                RelatedModelFactory(),
                RelatedModelFactory()
            ]
        )
        SimpleAuditRecord.objects.all().delete()
        obj.many_to_many.clear()
        record = SimpleAuditRecord.objects.get()

        self.assertEqual(
            record.changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [], 'old': 'ALL'}
        )

        self.assertEqual(self.user, record.changed_by)
