from .abstract_ws_pub_service import AbstractWSPubService
import logging
from ..utils import config
import traceback
import redis
import json
from datetime import datetime
import pytz
import time


class RedisWSPubService(AbstractWSPubService):

    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.StrictRedis \
                    (
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

    def __del__(self):
        if self.redis_client is not None:
            self.redis_client = None

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str):
        try:
            if self.redis_client:
                now = datetime.utcnow().replace(tzinfo=pytz.UTC)
                res = {
                    'summit_id': summit_id,
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'entity_operator': op,
                    'created_at': round(time.time() * 1000),
                }
                self.redis_client.publish(config('REDIS_PUB.CHANNEL'), json.dumps(res))
        except:
            self.redis_client = None
            logging.getLogger('api').warning(traceback.format_exc())
