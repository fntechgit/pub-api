import logging
import os
import shutil
import traceback

from celery import shared_task

from api.models import RedisWSPubService
from api.models import SupaBasePubService
from api.models.feeds_download_service import FeedsDownloadService
from api.models.feeds_upload_service import FeedsUploadService
from api.security.access_token_service import AccessTokenService
from django.core.cache import cache
from api.utils import config


@shared_task(bind=True)
def create_model_snapshot(self, summit_id: int):
    logging.getLogger('api')\
        .debug(f'calling create_model_snapshot task (id: {self.request.id}) for summit {summit_id}...')

    feeds_download_service = FeedsDownloadService(AccessTokenService())
    feeds_upload_service = FeedsUploadService(SupaBasePubService(), RedisWSPubService())

    feeds_download_service.download(summit_id, get_target_dir_path(summit_id, self.request.id))
    feeds_upload_service.upload(summit_id)

    clean_executed_task(summit_id)

    return f"Model synced for summit {summit_id}"


def get_target_dir_path(summit_id: int, task_id: int) -> str:
    summit_storage_path = os.path.join(config('LOCAL_SHOW_FEEDS_DIR_PATH'), summit_id.__str__())
    return os.path.join(summit_storage_path, task_id.__str__())


def create_snapshot_cancellable(summit_id: int):
    try:
        # check if there is running a task for this summit
        current_summit_task_id = cache.get(summit_id)

        # if so, revoke current task, clean up and run the new one
        if current_summit_task_id is not None:
            task = create_model_snapshot.AsyncResult(current_summit_task_id)
            task.abort()
            shutil.rmtree(get_target_dir_path(summit_id, current_summit_task_id))

        task = create_model_snapshot.delay(summit_id)

        # save summit_id and new background_task_id
        cache.set(summit_id, task.id)
    except Exception:
        logging.getLogger('create_snapshot').error(traceback.format_exc())


def clean_executed_task(summit_id: int):
    cache.delete(summit_id)
