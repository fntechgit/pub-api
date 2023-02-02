from django.test import TestCase
from ..models import PubManager, AblyPubService, SupaBasePubService
import time


class TestPubManager(TestCase):

    def test_publish(self):
        manager = PubManager()
        manager.add_service(AblyPubService())
        # manager.add_service(SupaBasePubService())
        created_at = round(time.time() * 1000)
        res = manager.pub(1, 1, "Presentation", "UPDATE", created_at)
        self.assertNotEqual(res, None)
