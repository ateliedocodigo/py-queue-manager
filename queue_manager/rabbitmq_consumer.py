# -*- coding: utf-8 -*-
"""
Inspired on `Asynchronous Cnsumer Example
<http://pika.readthedocs.io/en/0.13.1/examples/asynchronous_consumer_example.html>`_

.. code:: python

    single_url = 'amqp://username:password@hostname:port'
    # or multiple urls
    multiple_urls = (
        'amqp://username:password@hostnameone:port', 'amqp://username:password@hostnametwo:port'
    )
    consumer = RabbitMqConsumer(single_url, queue='queue_name')

    def callback(body):
        print("message body", body)

    try:
        consumer.start_listening(callback)
    except KeyboardInterrupt:
        consumer.stop()
"""
import logging
import sys
from inspect import signature

from queue_manager import QueueConsumer

try:
    import pika
except ModuleNotFoundError:
    raise ModuleNotFoundError("You need to install pika")

logger = logging.getLogger(__name__)


class RabbitMqConsumer(QueueConsumer):
    callback = None

    def __init__(self, amqp_urls,
                 exchange=None, exchange_type=None,
                 queue=None, queue_properties=None,
                 routing_key=None,
                 declare=True):

        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._urls = (amqp_urls,) if isinstance(amqp_urls, str) else amqp_urls
        self.urls = tuple(map(pika.URLParameters, self._urls))
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.queue = queue
        self.queue_properties = queue_properties
        self.routing_key = routing_key
        self.declare = declare

    def connect(self):
        logger.info('Connecting to %s', self._urls)

        return pika.SelectConnection.create_connection(self.urls, self.on_connection_open)

    def on_connection_open(self, connection):
        if isinstance(connection, Exception):
            logger.error(connection)
            sys.exit(1)
        logger.info('Connection opened')
        self._connection = connection
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        logger.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, error):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logger.warning('Connection closed, reopening in 5 seconds: (%r) %r', connection, error)
            self._connection.ioloop.call_later(5, self.reconnect)

    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:
            # Create a new connection
            workflow = self.connect()

            # There is now a new connection, needs a new ioloop to run
            workflow._nbio.run()

    def open_channel(self):
        logger.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        logger.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        if not self.declare:
            return self.on_bindok()
        self.setup_exchange()

    def add_on_channel_close_callback(self):
        logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, closing_reason):
        logger.error('Channel %s was closed: (%s)', channel, closing_reason)
        if not self._closing and self._connection.is_open:
            return self._connection.close()
        self._connection.ioloop.stop()

    def setup_exchange(self):
        if self.exchange:
            logger.info('Declaring exchange %s', self.exchange)
            self._channel.exchange_declare(callback=self.on_exchange_declareok,
                                           exchange=self.exchange,
                                           exchange_type=self.exchange_type)
            return
        self.on_exchange_declareok()

    def on_exchange_declareok(self, unused_frame=None):
        logger.info('Exchange declared')
        self.setup_queue()

    def setup_queue(self):
        if self.queue:
            logger.info('Declaring queue %s', self.queue)
            self._channel.queue_declare(callback=self.on_queue_declareok,
                                        queue=self.queue, arguments=self.queue_properties)

            return
        if self.exchange:
            self._channel.queue_declare(callback=self.on_queue_declareok,
                                        queue='', arguments=self.queue_properties, exclusive=True)
            return

        self.on_queue_declareok(None)

    def on_queue_declareok(self, method_frame):
        if self.exchange:
            if not self.queue:
                self.queue = method_frame.method.queue
            logger.info('Binding %s to %s with %s', self.exchange, self.queue, self.routing_key)
            self._channel.queue_bind(callback=self.on_bindok,
                                     queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)
            return
        self.on_bindok()

    def on_bindok(self, unused_frame=None):
        logger.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._channel.basic_qos(prefetch_count=1)
        self._consumer_tag = self._channel.basic_consume(on_message_callback=self.on_message, queue=self.queue)

    def add_on_cancel_callback(self):
        logger.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        logger.info('Consumer was cancelled remotely, shutting down: %r', method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, message):
        try:
            self.callback(message, properties)
            self.acknowledge_message(basic_deliver.delivery_tag)
        except KeyboardInterrupt as e:
            self.reject_message(basic_deliver.delivery_tag)
            raise e
        except Exception as e:
            logger.exception(e)
            self.reject_message(basic_deliver.delivery_tag, not basic_deliver.redelivered)

    def reject_message(self, delivery_tag, requeue=True):
        self._channel.basic_reject(delivery_tag, requeue)

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        if self._channel:
            logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        logger.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        logger.info('Closing the channel')
        self._channel.close()

    @staticmethod
    def validate_callback(callback):
        if 'properties' not in signature(callback).parameters:
            logger.warning('properties parameter missing on callback signature')
            return lambda message, properties: callback(message)
        return callback

    def run(self, callback=print):
        from warnings import warn
        warn('Deprecated, use start_listening instead', DeprecationWarning)
        return self.start_listening(callback)

    def start_listening(self, callback=print):
        self.callback = self.validate_callback(self.callback or callback)

        workflow = self.connect()
        workflow._nbio.run()

    def stop(self):
        logger.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        logger.info('Stopped')

    def close_connection(self):
        logger.info('Closing connection')
        self._closing = True
        self._connection.close()

    def ping(self):
        if self._connection is not None:
            return self._connection.is_open
        return pika.BlockingConnection(self.urls).is_open
