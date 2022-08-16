from abc import abstractmethod


class AbstractPubService:

    @abstractmethod
    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str):
        pass
