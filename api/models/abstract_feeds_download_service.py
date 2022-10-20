from abc import abstractmethod


class AbstractFeedsDownloadService:

    @abstractmethod
    def download(self, summit_id: int):
        pass
