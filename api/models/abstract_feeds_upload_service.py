from abc import abstractmethod


class AbstractFeedsUploadService:

    @abstractmethod
    def upload(self, summit_id: int):
        pass
