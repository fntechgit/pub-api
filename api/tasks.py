import logging

from celery import shared_task

from api.models.feeds_download_service import FeedsDownloadService
from api.models.feeds_upload_service import FeedsUploadService
from api.security.access_token_service import AccessTokenService


@shared_task
def create_model_snapshot(summit_id: int):
    logging.getLogger('api').debug(f'calling create_model_snapshot task for summit {summit_id}...')

    access_token_service = AccessTokenService()
    feeds_download_service = FeedsDownloadService(access_token_service)
    feeds_upload_service = FeedsUploadService()

    feeds_download_service.download(summit_id)
    feeds_upload_service.upload(summit_id)

    return f"Model synced for summit {summit_id}"
