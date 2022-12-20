from django.test import TestCase
from ..models import SupaBasePubService
import time


class TestSupabasePubService(TestCase):

    def test_publish(self):
        service = SupaBasePubService()
        created_at = round(time.time() * 1000)
        res = service.pub(1, 1, "Presentation", "INSERT", created_at)
        self.assertNotEqual(res, None)
