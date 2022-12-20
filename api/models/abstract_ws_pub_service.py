from abc import abstractmethod


class AbstractWSPubService:

    @abstractmethod
    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at:int):
        pass
