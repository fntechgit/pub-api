import json
import os

import boto3
import redis

from .abstract_feeds_upload_service import AbstractFeedsUploadService

import logging
from ..utils import config
import traceback


class FeedsUploadService(AbstractFeedsUploadService):

    def __init__(self):
        super().__init__()
        self.redis_client = None
        try:
            self.redis_client = redis.StrictRedis(
                config("REDIS_PUB.HOST"),
                config("REDIS_PUB.PORT"),
                password=config("REDIS_PUB.PASSWORD", None),
                charset="utf-8",
                decode_responses=True,
                db=config("REDIS_PUB.DB")
            )
        except:
            self.redis_client = None
            logging.getLogger('api').warning(traceback.format_exc())

    def upload(self, summit_id: int):
        try:
            session = boto3.session.Session()

            client = session.client(
                's3',
                region_name=config("STORAGE.REGION_NAME"),
                endpoint_url=config("STORAGE.ENDPOINT_URL"),
                aws_access_key_id=config("STORAGE.ACCESS_KEY_ID"),
                aws_secret_access_key=config("STORAGE.SECRET_ACCESS_KEY"),
            )

            show_feeds_dir_path = os.path.join(config('LOCAL_SHOW_FEEDS_DIR_PATH'), summit_id.__str__())

            responses = []

            for path in os.listdir(show_feeds_dir_path):
                # check if current path is a file
                if not os.path.isfile(os.path.join(show_feeds_dir_path, path)):
                    continue

                with open(os.path.join(show_feeds_dir_path, path), 'rb') as file_contents:
                    responses += client.put_object(
                        Bucket=f'{config("STORAGE.BUCKET_NAME")}',
                        Key=f'{summit_id}/{path}',
                        Body=file_contents,
                    )
                    logging.getLogger('api').info(f'FeedsUploadService uploading {summit_id}/{path}')

            # publish to redis

            if self.redis_client:
                self.redis_client.publish(config('REDIS_PUB.CHANNEL'), json.dumps(responses))

        except Exception:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsUploadService::upload error')
