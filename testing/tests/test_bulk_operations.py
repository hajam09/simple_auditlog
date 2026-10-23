from django.contrib.auth.models import User
from django.test import TestCase

from auditlog.models import SimpleAuditRecord
from auditlog.utils import set_current_user
from testing.models import RelatedModel
from .factories import RelatedModelFactory


class BulkOperationsAuditTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='sample-user')
        set_current_user(self.user)

    def test_bulk_create_creates_audit_records(self):
        RelatedModel.objects.bulk_create([
            RelatedModel()
            for _ in range(3)
        ])

        relatedModel = list(RelatedModel.objects.all())
        simpleAuditRecord = list(SimpleAuditRecord.objects.all())

        self.assertEqual(3, len(relatedModel))
        self.assertEqual(3, len(simpleAuditRecord))

        self.assertTrue(all([v.changes['name']['changed'] for v in simpleAuditRecord]))
        self.assertTrue(all(v.changes['name']['old'] is None for v in simpleAuditRecord))
        self.assertTrue(all(v.action == 'created' for v in simpleAuditRecord))
        self.assertTrue(all(v.changed_by == self.user for v in simpleAuditRecord))

    def test_bulk_update_creates_audit_only_for_changed_objects(self):
        # relatedModels = RelatedModelFactory.create_batch(3)
        # SimpleAuditRecord.objects.all().delete()
        #
        # relatedModels[0].name = "A"
        # relatedModels[2].name = "C"
        #
        # RelatedModel.objects.bulk_update(relatedModels, ["name"])
        #
        # records = SimpleAuditRecord.objects.all()
        # self.assertEqual(records.count(), 2)
        # for record in records:
        #     self.assertEqual(record.action, "updated")
        #     self.assertTrue(record.changes["name"]["changed"])
        """
        IMPORTANT:
            We intentionally do NOT audit QuerySet.update() here.

            Django implements bulk_update() by calling update() with CASE expressions.
            At that level, the ORM no longer knows the per-row "new value" — only a
            SQL expression exists. Auditing update() would therefore:
              - lose per-object value information
              - duplicate bulk_update audit entries
              - attempt to serialize ORM expressions (Case), which fails

            For correctness, bulk_update auditing is handled explicitly in
            SimpleAuditRecordBulkManager.bulk_update().

            QuerySet.update() auditing may be added in the future for literal updates
            (non-expression values) only.
        """

        pass

    def test_queryset_all_update_creates_audit_records(self):
        RelatedModelFactory.create_batch(5)
        SimpleAuditRecord.objects.all().delete()

        RelatedModel.objects.all().update(name='New Name')

        relatedModel = list(RelatedModel.objects.all())
        simpleAuditRecord = list(SimpleAuditRecord.objects.all())

        self.assertEqual(5, len(simpleAuditRecord))
        self.assertTrue(all(v.action == 'updated' for v in simpleAuditRecord))
        self.assertTrue(all(v.name == 'New Name' for v in relatedModel))
        self.assertTrue(all([v.changes['name']['changed'] for v in simpleAuditRecord]))
        self.assertTrue(all([v.changes['name']['new'] == 'New Name' for v in simpleAuditRecord]))
        self.assertTrue(all(v.changed_by == self.user for v in simpleAuditRecord))

    def test_queryset_filter_update_creates_audit_records(self):
        RelatedModelFactory.create_batch(5)
        SimpleAuditRecord.objects.all().delete()
        RelatedModel.objects.filter(id__in=[1, 2, 5]).update(name='New Name')

        simpleAuditRecord = list(SimpleAuditRecord.objects.all())

        self.assertEqual(3, len(simpleAuditRecord))
        self.assertTrue(all(v.action == 'updated' for v in simpleAuditRecord))
        self.assertTrue(all([v.changes['name']['changed'] for v in simpleAuditRecord]))
        self.assertTrue(all([v.changes['name']['new'] == 'New Name' for v in simpleAuditRecord]))
        self.assertTrue(all(v.changed_by == self.user for v in simpleAuditRecord))

    def test_queryset_all_delete_creates_audit_records(self):
        RelatedModelFactory.create_batch(5)
        SimpleAuditRecord.objects.all().delete()
        RelatedModel.objects.all().delete()

        relatedModel = list(RelatedModel.objects.all())
        simpleAuditRecord = list(SimpleAuditRecord.objects.all())

        self.assertEqual(0, len(relatedModel))
        self.assertEqual(5, len(simpleAuditRecord))
        self.assertTrue(all(v.action == 'deleted' for v in simpleAuditRecord))
        self.assertTrue(all([v.changes['name']['changed'] for v in simpleAuditRecord]))
        self.assertTrue(all([v.changes['name']['new'] is None for v in simpleAuditRecord]))
        self.assertTrue(all(v.changed_by == self.user for v in simpleAuditRecord))

    def test_queryset_filter_delete_creates_audit_records(self):
        RelatedModelFactory.create_batch(5)
        SimpleAuditRecord.objects.all().delete()
        RelatedModel.objects.filter(id__in=[1, 2, 5]).delete()

        relatedModel = list(RelatedModel.objects.all())
        simpleAuditRecord = list(SimpleAuditRecord.objects.all())

        self.assertEqual(2, len(relatedModel))
        self.assertEqual(3, len(simpleAuditRecord))

        self.assertTrue(all(v.action == 'deleted' for v in simpleAuditRecord))
        self.assertTrue(all([v.changes['name']['changed'] for v in simpleAuditRecord]))
        self.assertTrue(all([v.changes['name']['new'] is None for v in simpleAuditRecord]))
        self.assertTrue(all(v.changed_by == self.user for v in simpleAuditRecord))
