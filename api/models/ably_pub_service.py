import logging
from ..utils import config
import traceback
from .abstract_pub_service import AbstractPubService
from ably import AblyRest
import json
import asyncio

class AblyPubService(AbstractPubService):

    def __init__(self):
        self.client = None
        key: str = config("ABLY_API_KEY")

        try:
            self.client = AblyRest(key)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            raise Exception('AblyPubService connection error')

    def __del__(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    async def publish_on(self, channel, payload):
        await channel.publish(u'EVENT', payload)

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        try:
            if self.client:
                payload = {
                    'summit_id': summit_id,
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'entity_operator': op,
                    'created_at': created_at,
                }

                if summit_id > 0:
                    channel_name = '{summit_id}:*:*'.format(summit_id=summit_id)
                    logging.getLogger('api').debug(
                        'AblyPubService::pub publishing to channel {channel_name}'.format(channel_name=channel_name))

                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.publish_on(self.client.channels.get(channel_name), payload))
                    loop.close()

                    if entity_type and entity_id > 0:
                        channel_name = '{summit_id}:{entity_type}:{entity_id}'.format(summit_id=summit_id,
                                                                                      entity_type=entity_type,
                                                                                      entity_id=entity_id)
                        logging.getLogger('api').debug(
                            'AblyPubService::pub publishing to channel {channel_name}'.format(
                                channel_name=channel_name))

                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(
                            self.publish_on(self.client.channels.get(channel_name), payload))
                        loop.close()

                    return
        except:
            logging.getLogger('api').warning(traceback.format_exc())
