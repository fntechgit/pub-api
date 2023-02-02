from .abstract_pub_service import AbstractPubService
import logging
from ..utils import config
import traceback
import redis
import json


class RedisWSPubService(AbstractPubService):

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

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at:int):
        try:
            if self.redis_client:
                res = {
                    'summit_id': summit_id,
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'entity_operator': op,
                    'created_at': created_at,
                }
                self.redis_client.publish(config('REDIS_PUB.CHANNEL'), json.dumps(res))
        except:
            self.redis_client = None
            logging.getLogger('api').warning(traceback.format_exc())
