from django.test import TestCase
from ..models import SupaBasePubService


class TestSupabasePubService(TestCase):

    def test_publish(self):
        service = SupaBasePubService()
        res = service.pub(1, 1, "Presentation", "INSERT")
        self.assertNotEqual(res, None)
