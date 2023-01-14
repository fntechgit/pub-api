import logging
from ..utils import config
import traceback
from .abstract_pub_service import AbstractPubService
from ably import AblyRest
import asyncio
from threading import Thread

class AblyPubService(AbstractPubService):

    def __init__(self):
        self.key = config("ABLY_API_KEY")

    async def process_payload(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        logging.getLogger('api').debug(
            'AblyPubService::process_payload summit_id {summit_id} entity_id {entity_id} entity_type {entity_type}'.format(
                summit_id=summit_id, entity_id=entity_id, entity_type=entity_type))
        client = None
        try:
            client = AblyRest(self.key)
            if client:
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
                    channel = client.channels.get(channel_name)
                    await channel.publish(u'EVENT', payload)
                    client.channels.release(channel_name)
                    if entity_type and entity_id > 0:
                        channel_name = '{summit_id}:{entity_type}:{entity_id}'.format(summit_id=summit_id,
                                                                                      entity_type=entity_type,
                                                                                      entity_id=entity_id)
                        logging.getLogger('api').debug(
                            'AblyPubService::pub publishing to channel {channel_name}'.format(
                                channel_name=channel_name))

                        channel = client.channels.get(channel_name)
                        await channel.publish(u'EVENT', payload)
                        client.channels.release(channel_name)
        except:
            logging.getLogger('api').warning(traceback.format_exc())
        finally:
            if client:
                await client.close()

    def callback(self,loop, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        logging.getLogger('api').debug(
            'AblyPubService thread callback summit_id {summit_id} entity_id {entity_id} entity_type {entity_type}'.format(summit_id=summit_id,entity_id=entity_id,entity_type=entity_type))

        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.process_payload(summit_id , entity_id , entity_type, op, created_at))
        loop.close()

    def pub(self, summit_id: int, entity_id: int, entity_type: str, op: str, created_at: int):
        try:
            loop = asyncio.new_event_loop()
            t = Thread(target=self.callback, args=[loop, summit_id, entity_id, entity_type, op, created_at])
            t.start()
            t.join()
        except:
            logging.getLogger('api').warning(traceback.format_exc())
