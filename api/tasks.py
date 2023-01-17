import logging
import os
import shutil
import traceback

from celery import shared_task

from api.models import RedisWSPubService, PubManager, AblyPubService
from api.models import SupaBasePubService
from api.models.feeds_download_service import FeedsDownloadService
from api.models.feeds_upload_service import FeedsUploadService
from api.models.tasks_cache_wrapper import TasksCacheWrapper, TaskStatus
from api.security.access_token_service import AccessTokenService
from api.utils import config


@shared_task(bind=True)
def create_model_snapshot(self, summit_id: int):
    logging.getLogger('api')\
        .debug(f'calling create_model_snapshot task (id: {self.request.id}) for summit {summit_id}...')

    feeds_download_service = FeedsDownloadService(AccessTokenService())
    pivot_dir_path = get_local_pivot_dir_path(summit_id, self.request.id)
    feeds_download_service.download(summit_id, pivot_dir_path, self.request.id)
    logging.getLogger('api').debug(f'task {self.request.id} for summit {summit_id}: download stage completed')

    upload_latest_completed(summit_id)
    logging.getLogger('api').debug(f'task {self.request.id} for summit {summit_id}: upload stage completed')

    return f"Model synced for summit {summit_id}"


def upload_latest_completed(summit_id: int):
    # get the latest task between the completed ones (download completed)
    latest_completed_task = TasksCacheWrapper.get_latest_completed_task(summit_id)
    if latest_completed_task is None:
        return

    logging.getLogger('api') \
        .debug(f'task {latest_completed_task.id} for summit_id {summit_id} is ready for upload stage')

    pub_manager = PubManager()
    pub_manager.add_service(SupaBasePubService())
    pub_manager.add_service(RedisWSPubService())
    pub_manager.add_service(AblyPubService())

    feeds_upload_service = FeedsUploadService(pub_manager)
    pivot_dir_path = get_local_pivot_dir_path(summit_id, latest_completed_task.id)
    feeds_upload_service.upload(summit_id, pivot_dir_path)

    logging.getLogger('api') \
        .debug(f'task {latest_completed_task.id} for summit_id {summit_id} is uploaded')

    # nothing else to do with the rest of the downloads
    clean_up_tasks(summit_id)


def get_local_pivot_dir_path(summit_id: int, task_id: str) -> str:
    summit_storage_path = os.path.join(config('LOCAL_SHOW_FEEDS_DIR_PATH'), summit_id.__str__())
    return os.path.join(summit_storage_path, task_id.__str__())


def clean_up_tasks(summit_id: int):
    summit_completed_tasks = \
        TasksCacheWrapper.get_tasks_by_status(summit_id, [TaskStatus.CANCELLED, TaskStatus.DOWNLOADED])

    for task_id in summit_completed_tasks:
        logging.getLogger('api').debug(f'cleaning up task {task_id}....')

        task_dir_path = get_local_pivot_dir_path(summit_id, task_id)
        if os.path.exists(task_dir_path):
            logging.getLogger('api').debug(f'removing folder {task_dir_path}...')
            shutil.rmtree(task_dir_path, ignore_errors=True)

        TasksCacheWrapper.remove_task(summit_id, task_id)


def create_snapshot_cancellable(summit_id: int):
    try:
        # check if there are running tasks for this summit
        summit_running_tasks = TasksCacheWrapper.get_tasks_by_status(summit_id, [TaskStatus.DOWNLOADING])

        # if so, revoke current task, clean up and run the new one
        for task_id in summit_running_tasks:
            logging.getLogger('api') \
                .info(f'create_snapshot_cancellable - cancelling old task {task_id} for summit_id {summit_id}')
            task = create_model_snapshot.AsyncResult(task_id)
            task.revoke()
            TasksCacheWrapper.update_task_status(summit_id, task_id, TaskStatus.CANCELLED)

        task = create_model_snapshot.delay(summit_id)

        logging.getLogger('api').info(f'create_snapshot_cancellable - new task {task.id} for summit_id {summit_id}')

        TasksCacheWrapper.add_running_task(summit_id, task.id)
    except Exception as e:
        logging.getLogger('api').error(e)
        logging.getLogger('api').error(traceback.format_exc())
