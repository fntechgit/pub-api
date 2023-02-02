from abc import abstractmethod
from api.models import AbstractPubService


class AbstractPubManager:

    @abstractmethod
    def add_service(self, service: AbstractPubService):
        pass

    @abstractmethod
    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        pass
