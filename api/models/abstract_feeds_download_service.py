from abc import abstractmethod


class AbstractFeedsDownloadService:

    @abstractmethod
    def download(self, summit_id: int, target_dir: str, task_id: str):
        pass
