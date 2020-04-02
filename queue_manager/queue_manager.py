"""
.. code::

    from queue_manager.queue_manager import QueueManager
    conn_params = {
        'host': '',
        'port': '',
        'username': '',
        'password': ''
    }
    # or use multiple urls
    conn_params = ('amqp://host1', 'amqp://host2',)
    qm = QueueManager(conn_params)
    qm.push('hello', 'Hello from QueueManager')
    # True
    qm.pop('hello')
    # Hello from QueueManager
    del(qm)
"""
import logging

try:
    import pika
except ModuleNotFoundError:
    raise ModuleNotFoundError("You need to install pika")


class QueueManager:
    connection = None
    connection_parameters = {}
    logger = None

    def __init__(self, connection_parameters, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.logger.debug("init Queue Manager")
        self.logger.debug("connection parameters %s:%s", connection_parameters.get('host'),
                          connection_parameters.get('port'))
        self.connection_parameters = connection_parameters

    def __connect(self):
        if 'urls' in self.connection_parameters:
            self.connection = pika.BlockingConnection(
                tuple(map(pika.URLParameters, self.connection_parameters['urls']))
            )
            return

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
        """Disconnect when delete object."""
        self.logger.info("Finishing")
        self.__disconnect()
