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

    pivot_dir_path = get_local_pivot_dir_path(summit_id, self.request.id)

    feeds_download_service.download(summit_id, pivot_dir_path)
    feeds_upload_service.upload(summit_id, pivot_dir_path)

    clean_executed_task(summit_id, self.request.id)

    return f"Model synced for summit {summit_id}"


def get_local_pivot_dir_path(summit_id: int, task_id: str) -> str:
    summit_storage_path = os.path.join(config('LOCAL_SHOW_FEEDS_DIR_PATH'), summit_id.__str__())
    return os.path.join(summit_storage_path, task_id.__str__())


def create_snapshot_cancellable(summit_id: int):
    try:
        # check if there is running a task for this summit
        current_summit_task_id = cache.get(summit_id)

        # if so, revoke current task, clean up and run the new one
        if current_summit_task_id is not None:
            logging.getLogger('api') \
                .info(f'create_snapshot_cancellable - cancelling old task {current_summit_task_id} for summit_id {summit_id}')
            task = create_model_snapshot.AsyncResult(current_summit_task_id)
            task.revoke()
            clean_executed_task(summit_id, current_summit_task_id)

        task = create_model_snapshot.delay(summit_id)

        logging.getLogger('api') \
            .info(f'create_snapshot_cancellable - new task {task.id} for summit_id {summit_id}')

        # save summit_id and new background_task_id
        cache.set(summit_id, task.id)
    except Exception:
        logging.getLogger('api').error(traceback.format_exc())


def clean_executed_task(summit_id: int, task_id: str):
    task_dir_path = get_local_pivot_dir_path(summit_id, task_id)
    if os.path.exists(task_dir_path):
        shutil.rmtree(task_dir_path)

    cache.delete(summit_id)
