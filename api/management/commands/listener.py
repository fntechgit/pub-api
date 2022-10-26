from django.core.management.base import BaseCommand
import json
import pika
import logging

import traceback

from pika.exceptions import ConnectionClosedByBroker, AMQPChannelError, AMQPConnectionError

from api.utils import config

from phpserialize import unserialize
from phpserialize import phpobject

QUEUE_EVENT_NAME = 'App\\Jobs\\PublishScheduleEntityLifeCycleEvent'


class Command(BaseCommand):
    help = 'Runs Queue listener (RabbitMQ)'

    def __init__(self):
        super().__init__()

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
            if command_name == QUEUE_EVENT_NAME:
                dict = Command.php_serialized_to_dict(command)
                # received a novelty
                # summit_id
                # entity_id
                # entity_type
                # entity_operator (INSERT, UPDATE, DELETE)

                entity_op = dict['entity_operator']
                summit_id = dict['summit_id']
                entity_id = dict['entity_id']
                entity_type = dict['entity_type']

                logging.getLogger('listener').info('command {command_name} entity_op {entity_op} summit_id {summit_id} entity_id {entity_id}'.format(
                    command_name=command_name, entity_op=entity_op, summit_id=summit_id, entity_id={entity_id},
                    entity_type={entity_type}))

                # and trigger celery job to rebuild CDN json files
        except:
            logging.getLogger('listener').error(traceback.format_exc())

    def handle(self, *args, **kwargs):
        credentials = pika.PlainCredentials(config("RABBIT.USER"), config("RABBIT.PASSWORD") )
        while True:
            try:
                parameters = pika.ConnectionParameters \
                        (
                        host=config("RABBIT.HOST"),
                        port=config("RABBIT.PORT"),
                        virtual_host=config("RABBIT.VIRTUAL_HOST"),
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                connection = pika.BlockingConnection(parameters)
                print("Running Queue listener")
                channel = connection.channel()

                channel.exchange_declare(exchange=config("RABBIT.EXCHANGE"), exchange_type='fanout', durable=True,
                                         auto_delete=False)
                result = channel.queue_declare(queue=config("RABBIT.QUEUE"), exclusive=False, auto_delete=False,
                                               durable=True)

                queue_name = result.method.queue

                channel.queue_bind(exchange=config("RABBIT.EXCHANGE"), queue=queue_name)

                channel.basic_consume(queue_name, on_message_callback=self.callback, auto_ack=True)

                print("Started Consuming...")
                try:
                    channel.start_consuming()
                except KeyboardInterrupt:
                    print("Exiting command ...")
                    channel.stop_consuming()
                    connection.close()
                    break
            except ConnectionClosedByBroker:
                continue
            except AMQPChannelError as err:
                print("Caught a channel error: {}, stopping...".format(err))
                break
                # Recover on all other connection errors
            except AMQPConnectionError:
                print("Connection was closed, retrying...")
                continue
