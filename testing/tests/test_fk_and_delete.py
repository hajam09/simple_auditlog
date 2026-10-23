from django.contrib.auth.models import User
from django.test import TestCase

from auditlog.models import SimpleAuditRecord
from auditlog.utils import set_current_user
from .factories import ComprehensiveModelFactory, RelatedModelFactory


class ForeignKeyAndDeleteAuditTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='sample-user')
        set_current_user(self.user)

    def test_deleting_model_creates_delete_audit(self):
        obj = RelatedModelFactory()
        SimpleAuditRecord.objects.all().delete()

        obj_pk = obj.pk
        obj.delete()
        record = SimpleAuditRecord.objects.get()

        self.assertEqual(record.action, "deleted")
        self.assertEqual(record.object_id, str(obj_pk))
        for field, data in record.changes.items():
            self.assertTrue(data["changed"])
            self.assertIsNone(data["new"])

        self.assertEqual(self.user, record.changed_by)

    def test_cascade_delete_from_foreign_key_creates_audit(self):
        r1 = RelatedModelFactory()
        ComprehensiveModelFactory(foreign_key=r1)
        SimpleAuditRecord.objects.all().delete()

        r1.delete()
        records = list(SimpleAuditRecord.objects.all().order_by('changed_at'))

        self.assertEqual(2, len(records))

        self.assertEqual('deleted', records[0].action)
        self.assertEqual('deleted', records[1].action)

        self.assertEqual(records[0].changes['name'], {'changed': True, 'new': None, 'old': r1.name})
        for k, v in records[1].changes.items():
            self.assertTrue(v['changed'])
            self.assertIsNone(v['new'])

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_one_to_one_delete_cascades_and_creates_audit(self):
        r1 = RelatedModelFactory()
        ComprehensiveModelFactory(one_to_one=r1)
        SimpleAuditRecord.objects.all().delete()

        r1.delete()
        records = list(SimpleAuditRecord.objects.all().order_by('changed_at'))

        self.assertEqual(2, len(records))

        self.assertEqual('deleted', records[0].action)
        self.assertEqual('deleted', records[1].action)

        self.assertEqual(records[0].changes['name'], {'changed': True, 'new': None, 'old': r1.name})
        for k, v in records[1].changes.items():
            self.assertTrue(v['changed'])
            self.assertIsNone(v['new'])

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_deleting_related_model_does_not_create_duplicate_audits(self):
        r1 = RelatedModelFactory()
        obj = ComprehensiveModelFactory(foreign_key=r1)
        SimpleAuditRecord.objects.all().delete()

        obj.foreign_key.delete()

        self.assertEqual(SimpleAuditRecord.objects.count(), 2)

    def test_object_id_is_string_on_delete(self):
        r1 = RelatedModelFactory()
        obj = ComprehensiveModelFactory(foreign_key=r1)
        SimpleAuditRecord.objects.all().delete()

        pk = obj.pk
        obj.delete()

        record = SimpleAuditRecord.objects.get()
        self.assertIsInstance(record.object_id, str)
        self.assertEqual(record.object_id, str(pk))

        self.assertEqual(self.user, record.changed_by)
