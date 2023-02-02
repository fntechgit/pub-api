import sys
import time
from asyncio import Future
from enum import Enum
from typing import Optional, List

from django.core.cache import cache


def dump_if_task_still_active(func):
    def wrapper(*args, **kwargs):
        task_id = kwargs['task_id']

        if task_id == "0":
            func(*args, **kwargs)
            return

        task = TasksCacheWrapper.get_task_by_id(kwargs['summit_id'], task_id)
        if task is not None and task.status == TaskStatus.DOWNLOADING:
            func(*args, **kwargs)

    return wrapper


def download_if_task_still_active(func):
    def wrapper(*args, **kwargs):
        task_id = kwargs['task_id']

        if task_id == "0":
            return func(*args, **kwargs)

        task = TasksCacheWrapper.get_task_by_id(kwargs['summit_id'], task_id)
        if task is not None and task.status == TaskStatus.DOWNLOADING:
            return func(*args, **kwargs)

        res = Future()
        res.set_result([])
        return res

    return wrapper


class TaskStatus(Enum):
    DOWNLOADING = 1
    DOWNLOADED = 2
    CANCELLED = 3


class TaskInfo:
    def __init__(self, task_id: str, age: float, status: TaskStatus) -> None:
        self.id = task_id
        self.age = age
        self.status = status


class TasksCacheWrapper:

    @staticmethod
    def get_tasks_by_status(summit_id: int, statuses: List[TaskStatus]) -> {}:
        tasks_info = cache.get(summit_id)
        if tasks_info is None:
            return {}
        return dict(filter(lambda elem: elem[1].status in statuses, tasks_info.items()))

    @staticmethod
    def get_task_by_id(summit_id: int, task_id: str) -> Optional[TaskInfo]:
        tasks_info = cache.get(summit_id)
        if tasks_info is not None and task_id in tasks_info:
            return tasks_info[task_id]
        return None

    @staticmethod
    def get_latest_completed_task(summit_id: int) -> Optional[TaskInfo]:
        tasks_info = cache.get(summit_id)
        latest_completed_task = None
        latest_age = sys.float_info.max

        for value in tasks_info.values():
            if value.status == TaskStatus.DOWNLOADED and value.age < latest_age:
                latest_age = value.age
                latest_completed_task = value

        return latest_completed_task

    @staticmethod
    def add_running_task(summit_id: int, task_id: str):
        tasks_info = cache.get(summit_id)
        if tasks_info is None:
            tasks_info = {}
        tasks_info[task_id] = TaskInfo(task_id, time.time(), TaskStatus.DOWNLOADING)
        cache.set(summit_id, tasks_info)

    @staticmethod
    def update_task_status(summit_id: int, task_id: str, status: TaskStatus):
        tasks_info = cache.get(summit_id)
        if tasks_info is not None and task_id in tasks_info:
            tasks_info[task_id].status = status
            cache.set(summit_id, tasks_info)

    @staticmethod
    def remove_task(summit_id: int, task_id: str):
        tasks_info = cache.get(summit_id)
        if tasks_info is not None and task_id in tasks_info:
            del tasks_info[task_id]
            cache.set(summit_id, tasks_info)

    @staticmethod
    def clear_summit_tasks(summit_id: int):
        cache.delete(summit_id)
