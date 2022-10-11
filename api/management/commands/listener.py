from django.core.management.base import BaseCommand
import json
import pika
import logging

import traceback
import sys

from api.utils import config


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
    def callback(channel, method, header, body):
        logging.getLogger('listener').info('receiving data')
        print(body)
        data = json.loads(body)
        print(data)

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
