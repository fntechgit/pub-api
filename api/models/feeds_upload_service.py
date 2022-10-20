import os

import boto3

from .abstract_feeds_upload_service import AbstractFeedsUploadService

import logging
from ..utils import config
import traceback


class FeedsUploadService(AbstractFeedsUploadService):

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

            show_feeds_dir_path = config('LOCAL_SHOW_FEEDS_DIR_PATH')

            for path in os.listdir(show_feeds_dir_path):
                # check if current path is a file
                if not os.path.isfile(os.path.join(show_feeds_dir_path, path)):
                    continue

                with open(os.path.join(show_feeds_dir_path, path), 'rb') as file_contents:
                    response = client.put_object(
                        Bucket=config("STORAGE.BUCKET_NAME"),
                        Key=path,
                        Body=file_contents,
                    )
                    logging.getLogger('api').info(f'FeedsUploadService upload - response {response}')

        except Exception:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('S3 error')
