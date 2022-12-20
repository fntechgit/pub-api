from django.core.management.base import BaseCommand
import json
import pika
import logging
import time
import traceback

from pika.exceptions import ConnectionClosedByBroker, AMQPChannelError, AMQPConnectionError

from api.tasks import create_snapshot_cancellable
from api.utils import config
from django_injector import inject
from api.models.abstract_pub_service import AbstractPubService
from api.models.abstract_ws_pub_service import AbstractWSPubService

QUEUE_EVENT_NAME = 'App\\Jobs\\PublishScheduleEntityLifeCycleEvent'


class Command(BaseCommand):
    help = 'Runs Queue listener (RabbitMQ)'

    @inject
    def __init__(self, service: AbstractPubService, ws_service: AbstractWSPubService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service
        self.ws_service = ws_service

    def callback(self, channel, method, header, body):
        try:
            logging.getLogger('listener').info('receiving data {data}'.format(data=body))
            data = json.loads(body)
            # received a novelty
            # summit_id
            # entity_id
            # entity_type
            # entity_operator (INSERT, UPDATE, DELETE)
            entity_op = data['entity_operator']
            summit_id = data['summit_id']
            entity_id = data['entity_id']
            entity_type = data['entity_type']
            created_at = round(time.time() * 1000)
            # trigger celery job to rebuild CDN json files
            if entity_type == 'Summit':
                summit_id = entity_id

            self.service.pub(summit_id, entity_id, entity_type, entity_op, created_at)

            # publish to WS

            self.ws_service.pub(summit_id, entity_id, entity_type, entity_op, created_at)

            create_snapshot_cancellable(summit_id)

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

                channel.queue_bind(exchange=config("RABBIT.EXCHANGE"), queue=queue_name, routing_key='')

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
