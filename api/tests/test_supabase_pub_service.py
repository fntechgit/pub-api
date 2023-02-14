from django.test import TestCase
from ..models import SupaBasePubService
import time


class TestSupabasePubService(TestCase):

    def test_publish(self):
        service = SupaBasePubService()
        created_at = round(time.time() * 1000)
        res = service.pub(40, 1, "Presentation", "UPDATE", created_at)
        self.assertNotEqual(res, None)

    def test_purge(self):
        service = SupaBasePubService()
        res = service.purge_entity_updates(24)
        self.assertNotEqual(res, None)
