# -*- coding: utf-8 -*-
import logging
import warnings

import pika


class QueueManager(object):
    connection = None
    connection_parameters = {}
    logger = None

    def __init__(self, connection_parameters, queue_args=None, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.logger.debug("init Queuer Manager")
        self.logger.debug("connection parameters %s:%s", connection_parameters.get('host'),
                          connection_parameters.get('port'))
        self.connection_parameters = connection_parameters
        if queue_args:
            self.logger.warning("Deprecated parameter queue_args")
            warnings.warn("Deprecated parameter queue_args", DeprecationWarning)

    def __connect(self):
        credentials = pika.PlainCredentials(
            self.connection_parameters.get('username'),
            self.connection_parameters.get('password')
        )
        parameters = pika.ConnectionParameters(
            host=self.connection_parameters.get('host'),
            port=self.connection_parameters.get('port'),
            virtual_host='/',
            credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)

    def __get_channel(self, queue_name=None, queue_args=None):
        if not self.connection:
            self.__connect()
        self.logger.debug("getting channel")
        channel = self.connection.channel()

        if queue_name:
            if queue_args:
                self.logger.debug('Declare queue %s',
                                  channel.queue_declare(queue=queue_name, arguments=queue_args))
            else:
                self.logger.debug('Declare queue %s', channel.queue_declare(queue=queue_name))

        return channel

    def push(self, queue_name, body, queue_args=None, pika_properties=None):
        channel = self.__get_channel(queue_name, queue_args)
        self.logger.debug("pushing %s to queue %s", body, queue_name)
        ret = channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=body,
            properties=pika_properties
        )
        self.logger.debug("pushed %s to queue %s return(%r)", body, queue_name, ret)
        self.__disconnect()
        return ret

    def pop(self, queue_name, queue_args=None):
        channel = self.__get_channel(queue_name, queue_args)
        self.logger.debug("pop from queue %s", queue_name)

        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        self.logger.debug("method_frame.NAME (%s)", method_frame.NAME if method_frame else '')
        if method_frame and method_frame.NAME == 'Basic.GetOk':
            self.logger.debug("[x] Received %r" % body)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)

        self.__disconnect()
        return body

    def ping(self):
        if not self.connection:
            self.__connect()
        return self.connection.is_open

    def __disconnect(self):
        if self.connection:
            self.logger.debug("disconnecting")
            self.logger.debug(self.connection.close())
            self.connection = None

    def __del__(self):
        """Disconnect when delete objet."""
        self.logger.info("Finishing")
        self.__disconnect()
