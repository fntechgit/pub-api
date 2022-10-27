import logging

from celery import shared_task

from api.models.abstract_feeds_download_service import AbstractFeedsDownloadService
from api.models.abstract_feeds_upload_service import AbstractFeedsUploadService


@shared_task
def create_model_snapshot(summit_id: int,
                          feeds_download_service: AbstractFeedsDownloadService,
                          feeds_upload_service: AbstractFeedsUploadService):
    logging.getLogger('api').debug(f'calling create_model_snapshot task for summit {summit_id}...')
    feeds_download_service.download(summit_id)
    feeds_upload_service.upload(summit_id)

    return f"Model synced for summit {summit_id}"
