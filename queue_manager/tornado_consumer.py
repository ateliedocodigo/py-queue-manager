"""
.. code:: python

    from tornado.ioloop import IOLoop
    from queue_manager.tornado_consumer import TornadoConsumer

    consumer = TornadoConsumer('amqp://username:password@hostname:port',
                               'exchange', 'exchange_type', 'queue_name', 'routing_key')


    def callback(body):
        print("message body", body)

    consumer.start_listening(callback)
    IOLoop.instance().start()
"""
import logging

from queue_manager.rabbitmq_consumer import RabbitMqConsumer

try:
    import pika
    from pika.adapters.tornado_connection import TornadoConnection
    from tornado.ioloop import IOLoop
except ModuleNotFoundError:
    tornado_installed = False
else:
    tornado_installed = True

logger = logging.getLogger(__name__)


class TornadoConsumer(RabbitMqConsumer):

    def __init__(self, *args, **kwargs):
        if not tornado_installed:
            raise Exception('Invalid consumer, tornado is not installed')
        super(TornadoConsumer, self).__init__(*args, **kwargs)

    def connect(self):
        logger.info('Connecting to %s', self._urls)
        urls = tuple(map(pika.URLParameters, self._urls))
        return TornadoConnection.create_connection(urls, self.on_connection_open)

    def reconnect(self):
        if self._closing:
            return

        # Create a new connection
        self.connect()

    def start_listening(self, callback=print):
        self.callback = self.validate_callback(self.callback or callback)
        IOLoop.instance().add_timeout(5000, self.connect)
