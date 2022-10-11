from django.core.management.base import BaseCommand
import json
import pika
import logging

import traceback
import sys

from api.utils import config

from phpserialize import unserialize
from phpserialize import phpobject


class Command(BaseCommand):
    help = 'Runs Queue listener'

    def __init__(self):
        super().__init__()
        try:
            credentials = pika.PlainCredentials(config("RABBIT.USER"), config("RABBIT.PASSWORD"), )
            parameters = pika.ConnectionParameters \
                    (
                    host=config("RABBIT.HOST"),
                    port=config("RABBIT.PORT"),
                    virtual_host=config("RABBIT.VIRTUAL_HOST"),
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            self.connection = pika.BlockingConnection(parameters)
        except:
            logging.getLogger('listener').error(traceback.format_exc())

    @staticmethod
    def php_serialized_to_dict(serialized):

        output = unserialize(bytes(serialized, 'utf-8'), object_hook=phpobject)

        output = output._asdict()

        output = {
            key.decode(): val.decode() if isinstance(val, bytes) else val
            for key, val in output.items()
        }

        return output

    @staticmethod
    def callback(channel, method, header, body):
        try:
            logging.getLogger('listener').info('receiving data {data}'.format(data=body))
            data = json.loads(body)
            command = data['data']['command']
            command_name = data['data']['commandName']
            logging.getLogger('listener').info('command {command_name}'.format(command_name=command_name))
            dict = Command.php_serialized_to_dict(command)
            # received a novelty
            # summit_id
            # entity_id
            # entity_type
            # operator (INSERT, UPDATE, DELETE)
            # here publish real time update to redis
            # and trigger celery job to rebuild CDN json files
        except:
            logging.getLogger('listener').error(traceback.format_exc())

    def handle(self, *args, **kwargs):
        try:
            print("Running Queue listener")
            channel = self.connection.channel()

            channel.exchange_declare(exchange=config("RABBIT.EXCHANGE"), exchange_type='fanout', durable=True,
                                     auto_delete=True)
            result = channel.queue_declare(queue=config("RABBIT.QUEUE"), exclusive=False, auto_delete=True,
                                           durable=True)

            queue_name = result.method.queue

            channel.queue_bind(exchange=config("RABBIT.EXCHANGE"), queue=queue_name)

            channel.basic_consume(queue_name, on_message_callback=self.callback, auto_ack=True)

            print("Started Consuming...")
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Exiting command ...")

            self.connection.close()
            sys.exit()
