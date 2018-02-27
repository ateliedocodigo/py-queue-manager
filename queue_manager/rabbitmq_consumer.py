# -*- coding: utf-8 -*-
"""Inspired on: http://pika.readthedocs.io/en/0.10.0/examples/asynchronous_consumer_example.html"""
import logging

import pika


class RabbitMqConsumer(object):
    def __init__(self, amqp_url,
                 exchange=None, exchange_type=None,
                 queue=None, queue_properties=None,
                 routing_key=None):

        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.queue = queue
        self.queue_properties = queue_properties
        self.routing_key = routing_key
        self.logger = logging.getLogger(self.__module__)

    def connect(self):
        self.logger.info('Connecting to %s', self._url)
        return pika.SelectConnection(pika.URLParameters(self._url), self.on_connection_open, stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        self.logger.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        self.logger.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            self.logger.warning('Connection closed, reopening in 5 seconds: (%s) %s', reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:
            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def open_channel(self):
        self.logger.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self.logger.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange()

    def add_on_channel_close_callback(self):
        self.logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self.logger.warning('Channel %i was closed: (%s) %s', channel, reply_code, reply_text)
        if not self._closing:
            self._connection.close()

    def setup_exchange(self):
        if self.exchange:
            self.logger.info('Declaring exchange %s', self.exchange)
            self._channel.exchange_declare(self.on_exchange_declareok, self.exchange, self.exchange_type)
            return
        self.on_exchange_declareok(None)

    def on_exchange_declareok(self, unused_frame):
        self.logger.info('Exchange declared')
        self.setup_queue()

    def setup_queue(self):
        if self.queue:
            self.logger.info('Declaring queue %s', self.queue)
            self._channel.queue_declare(self.on_queue_declareok, self.queue, arguments=self.queue_properties)

            return
        if self.exchange:
            self._channel.queue_declare(self.on_queue_declareok, arguments=self.queue_properties, exclusive=True)
            return

        self.on_queue_declareok(None)

    def on_queue_declareok(self, method_frame):
        if self.exchange:
            if not self.queue:
                self.queue = method_frame.method.queue
            self.logger.info('Binding %s to %s with %s', self.exchange, self.queue, self.routing_key)
            self._channel.queue_bind(self.on_bindok, self.queue, self.exchange, self.routing_key)
            return
        self.on_bindok(None)

    def on_bindok(self, unused_frame):
        self.logger.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        self.logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._channel.basic_qos(prefetch_count=1)
        self._consumer_tag = self._channel.basic_consume(self.on_message, self.queue)

    def add_on_cancel_callback(self):
        self.logger.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        self.logger.info('Consumer was cancelled remotely, shutting down: %r', method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        try:
            self.callback(body)
            self.acknowledge_message(basic_deliver.delivery_tag)
        except (KeyboardInterrupt, SystemExit) as e:
            self.reject_message(basic_deliver.delivery_tag)
            raise e
        except Exception as e:
            self.logger.error(e, exc_info=True)
            self.reject_message(basic_deliver.delivery_tag)

    def reject_message(self, delivery_tag):
        self._channel.basic_reject(delivery_tag)

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        if self._channel:
            self.logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        self.logger.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        self.logger.info('Closing the channel')
        self._channel.close()

    def run(self, callback=print):
        self.callback = callback

        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        self.logger.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        self.logger.info('Stopped')

    def close_connection(self):
        self.logger.info('Closing connection')
        self._closing = True
        self._connection.close()
