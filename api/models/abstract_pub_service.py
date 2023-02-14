from abc import abstractmethod


class AbstractPubService:

    @abstractmethod
    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        pass

    @abstractmethod
    def purge_entity_updates(self, hours_from_backward: int):
        pass
