from django.contrib.auth.models import User
from django.test import TestCase

from auditlog.models import SimpleAuditRecord
from auditlog.utils import set_current_user
from .factories import (
    ComprehensiveModelFactory,
    RelatedModelFactory,
)


class ComprehensiveFieldAuditTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='sample-user')
        set_current_user(self.user)

    def test_create_audits_all_native_fields_only(self):
        obj = ComprehensiveModelFactory()
        record = SimpleAuditRecord.objects.get()
        changes = record.changes

        self.assertEqual(str(obj.id), record.object_id)
        self.assertEqual(obj, record.content_object)
        self.assertEqual('created', record.action)

        for k, v in changes.items():
            self.assertIsNone(v['old'])
            self.assertTrue(v['changed'])

        # ---- Core fields ----
        self.assertEqual(changes["char"]["new"], "char value")
        self.assertEqual(changes["text"]["new"], "some long text")
        self.assertEqual(changes["boolean"]["new"], True)
        self.assertEqual(changes["integer"]["new"], -10)
        self.assertEqual(changes["positive_integer"]["new"], 10)
        self.assertEqual(changes["positive_big_integer"]["new"], 100000)
        self.assertEqual(changes["positive_small_integer"]["new"], 5)
        self.assertEqual(changes["big_integer"]["new"], 9999999999)
        self.assertEqual(changes["small_integer"]["new"], -5)
        self.assertAlmostEqual(changes["float_field"]["new"], 3.14159)
        self.assertEqual(changes["decimal"]["new"], 9.99)

        # ---- Date & time ----
        self.assertIsInstance(changes["date"]["new"], str)
        self.assertIsInstance(changes["datetime"]["new"], str)
        self.assertIsInstance(changes["time"]["new"], str)
        self.assertEqual(changes["duration"]["new"], 120.0)

        # ---- Other fields ----
        self.assertEqual(changes["json"]["new"]["nested"]["a"], 1)
        self.assertEqual(changes["email"]["new"], "test@example.com")
        self.assertEqual(changes["url"]["new"], "https://example.com")
        self.assertEqual(changes["slug"]["new"], "test-slug")
        self.assertIsInstance(changes["file_path"]["new"], str)
        self.assertEqual(changes["ip_address"]["new"], "127.0.0.1")
        self.assertEqual(changes["binary"]["new"], str(b"\x00\x01\x02"))
        self.assertEqual(changes["uuid"]["new"], "3fa85f64-5717-4562-b3fc-2c963f66afa6")

        self.assertEqual(self.user, record.changed_by)

    def test_create_audits_fk_field_only(self):
        r1 = RelatedModelFactory()
        ComprehensiveModelFactory(foreign_key=r1)

        records = SimpleAuditRecord.objects.all().order_by('changed_at')

        self.assertEqual(2, len(records))

        self.assertEqual('created', records[0].action)
        self.assertEqual(records[0].changes['name'], {'changed': True, 'new': r1.name, 'old': None})

        self.assertEqual('created', records[1].action)
        self.assertEqual(records[1].changes['foreign_key'], {'changed': True, 'new': r1.name, 'old': None})

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_create_audits_one_to_one_field_only(self):
        r1 = RelatedModelFactory()
        ComprehensiveModelFactory(one_to_one=r1)

        records = SimpleAuditRecord.objects.all().order_by('changed_at')

        self.assertEqual(2, len(records))

        self.assertEqual('created', records[0].action)
        self.assertEqual(records[0].changes['name'], {'changed': True, 'new': r1.name, 'old': None})

        self.assertEqual('created', records[1].action)
        self.assertEqual(records[1].changes['one_to_one'], {'changed': True, 'new': r1.name, 'old': None})

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_create_audits_many_to_many_field_only(self):
        r1 = RelatedModelFactory()
        r2 = RelatedModelFactory()
        ComprehensiveModelFactory(
            many_to_many=[
                r1,
                r2
            ]
        )

        records = SimpleAuditRecord.objects.all().order_by('changed_at')

        self.assertEqual(4, len(records))

        self.assertEqual('created', records[0].action)
        self.assertEqual(records[0].changes['name'], {'changed': True, 'new': r1.name, 'old': None})

        self.assertEqual('created', records[1].action)
        self.assertEqual(records[1].changes['name'], {'changed': True, 'new': r2.name, 'old': None})

        self.assertEqual('updated', records[3].action)
        self.assertEqual(
            records[3].changes['comprehensivemodel_many_to_many'],
            {'changed': True, 'new': [r1.pk, r2.pk], 'old': []}
        )

        self.assertTrue(all(v.changed_by == self.user for v in records))

    def test_update_only_marks_modified_fields(self):
        obj = ComprehensiveModelFactory(char="A", integer=1)
        SimpleAuditRecord.objects.all().delete()

        obj.char = "B"
        obj.integer = 1  # unchanged
        obj.save()

        record = SimpleAuditRecord.objects.get()

        self.assertEqual('updated', record.action)
        self.assertTrue(record.changes["char"]["changed"])
        self.assertEqual(record.changes["char"]["new"], "B")
        self.assertEqual(record.changes["char"]["old"], "A")

        self.assertFalse(record.changes["integer"]["changed"])
        self.assertEqual(record.changes["integer"]["new"], 1)
        self.assertEqual(record.changes["integer"]["old"], 1)

        self.assertEqual(self.user, record.changed_by)

    def test_noop_save_creates_no_audit_record(self):
        obj = ComprehensiveModelFactory()
        SimpleAuditRecord.objects.all().delete()

        obj.save()
        self.assertFalse(SimpleAuditRecord.objects.exists())
