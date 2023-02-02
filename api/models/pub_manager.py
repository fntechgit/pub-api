from api.models import AbstractPubService
from api.models.abstract_pub_manager import AbstractPubManager


class PubManager(AbstractPubManager):

    def __init__(self):
        self._services = []

    def add_service(self, service: AbstractPubService):
        self._services.append(service)

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        for service in self._services:
            service.pub(summit_id, entity_id, entity_type, op, created_at)
