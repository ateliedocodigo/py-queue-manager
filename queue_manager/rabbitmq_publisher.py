# -*- coding: utf-8 -*-
"""Inspired on: http://pika.readthedocs.io/en/0.10.0/examples/asynchronous_publisher_example.html"""
import logging

import pika


class RabbitMqPublisher(object):
    def __init__(self, amqp_url, exchange, exchange_type, queue, routing_key):
        self._connection = None
        self._channel = None
        self._closing = False
        self._stopping = False
        self._url = amqp_url
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.queue = queue
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
        self.setup_exchange(self.exchange)

    def add_on_channel_close_callback(self):
        self.logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self.logger.warning('Channel %i was closed: (%s) %s', channel, reply_code, reply_text)
        if not self._closing:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        self.logger.info('Declaring exchange %s', exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok, exchange_name, self.exchange_type)

    def on_exchange_declareok(self, unused_frame):
        self.logger.info('Exchange declared')
        self.setup_queue(self.queue)

    def setup_queue(self, queue_name):
        self.logger.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        self.logger.info('Binding %s to %s with %s', self.exchange, self.queue, self.routing_key)
        self._channel.queue_bind(self.on_bindok, self.queue, self.exchange, self.routing_key)

    def on_bindok(self, unused_frame):
        self.logger.info('Queue bound')

    def publish_message(self, message):
        if self._stopping:
            return

        properties = pika.BasicProperties(app_id='example-publisher', content_type='application/json')

        self._channel.basic_publish(self.exchange, self.routing_key, message, properties)

    def close_channel(self):
        self.logger.info('Closing the channel')
        if self._channel:
            self._channel.close()

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        self.logger.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.start()
        self.logger.info('Stopped')

    def close_connection(self):
        self.logger.info('Closing connection')
        self._closing = True
        self._connection.close()
