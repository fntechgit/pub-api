from api.tasks import create_model_snapshot
from django.core.cache import cache


def create_snapshot(summit_id: int):
    # check if there is running a task for this summit
    current_summit_task_id = cache.get(summit_id)

    # if so, revoke current task, clean up and run the new one
    if current_summit_task_id is not None:
        task = create_model_snapshot.AsyncResult(current_summit_task_id)
        task.abort()

    task = create_model_snapshot.delay(summit_id)

    # save summit_id and new background_task_id
    cache.set(summit_id, task.id)
