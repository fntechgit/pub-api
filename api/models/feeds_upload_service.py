import gzip
import logging
import os
import traceback
import hashlib
import boto3
import base64

from . import AbstractWSPubService, AbstractPubService
from .abstract_feeds_upload_service import AbstractFeedsUploadService
from ..utils import config

SCHEDULE_ENTITY_TYPE = 'Schedule'
SCHEDULE_ENTITY_OP = 'UPDATE'
SCHEDULE_ENTITY_ID = 0
S3_ACL = 'public-read'
S3_ContentType = 'application/json; charset=utf-8'
S3_ContentEncoding = 'gzip'


class FeedsUploadService(AbstractFeedsUploadService):

    def __init__(self, pub_service: AbstractPubService, ws_service: AbstractWSPubService):
        super().__init__()
        self.ws_service = ws_service
        self.pub_service = pub_service

    @staticmethod
    def get_content_md5(data):
        digest = hashlib.md5(data).digest()
        return base64.b64encode(digest)

    def upload(self, summit_id: int, source_dir_path: str):
        try:
            session = boto3.session.Session()

            client = session.client(
                's3',
                region_name=config("STORAGE.REGION_NAME"),
                endpoint_url=config("STORAGE.ENDPOINT_URL"),
                aws_access_key_id=config("STORAGE.ACCESS_KEY_ID"),
                aws_secret_access_key=config("STORAGE.SECRET_ACCESS_KEY"),
            )

            for path in os.listdir(source_dir_path):
                # check if current path is a file
                if not os.path.isfile(os.path.join(source_dir_path, path)):
                    continue

                with open(os.path.join(source_dir_path, path), 'rb') as file_contents:

                    body = gzip.compress(file_contents.read())
                    content_md5 = self.get_content_md5(body)
                    content_md5_string = content_md5.decode('utf-8')
                    client.put_object(
                        Bucket=f'{config("STORAGE.BUCKET_NAME")}',
                        Key=f'{summit_id}/{path}',
                        Body=body,
                        ACL=S3_ACL,
                        ContentEncoding=S3_ContentEncoding,
                        ContentType=S3_ContentType,
                        ContentMD5=content_md5_string,
                    )

                    logging.getLogger('api').info(f'FeedsUploadService uploading {source_dir_path}/{path}')

                # publish to WS

                self.pub_service.pub(summit_id, SCHEDULE_ENTITY_ID, SCHEDULE_ENTITY_TYPE, SCHEDULE_ENTITY_OP)
                self.ws_service.pub(summit_id, SCHEDULE_ENTITY_ID, SCHEDULE_ENTITY_TYPE, SCHEDULE_ENTITY_OP)

        except Exception as e:
            logging.getLogger('api').error(e)
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('FeedsUploadService::upload error')
