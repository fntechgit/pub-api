import os

import boto3

from . import AbstractWSPubService
from .abstract_feeds_upload_service import AbstractFeedsUploadService

import logging
from ..utils import config
import traceback


class FeedsUploadService(AbstractFeedsUploadService):

    def __init__(self, ws_service: AbstractWSPubService):
        super().__init__()
        self.ws_service = ws_service

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
                        ACL='public-read'
                    )
                    logging.getLogger('api').info(f'FeedsUploadService uploading {summit_id}/{path}')

                # publish to WS

                self.ws_service.pub(summit_id, 0, 'Schedule', 'UPDATE')

        except Exception as e:
            logging.getLogger('api').error(e)
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsUploadService::upload error')