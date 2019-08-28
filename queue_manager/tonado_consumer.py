import pika
import sys

from queue_manager.rabbitmq_consumer import RabbitMqConsumer

try:
    from pika.adapters.tornado_connection import TornadoConnection
    from tornado.ioloop import IOLoop
except ModuleNotFoundError:
    tornado_installed = False
else:
    tornado_installed = True


class TornadoConsumer(RabbitMqConsumer):
    callback = None

    def __init__(self, *args, **kwargs):
        if not tornado_installed:
            raise Exception('Invalid consumer, tornado is not installed')
        super(TornadoConsumer, self).__init__(*args, **kwargs)

    def connect(self):
        self.logger.info('Connecting to %s', self._urls)
        urls = tuple(map(pika.URLParameters, self._urls))
        return TornadoConnection.create_connection(urls, self.on_connection_open)

    def reconnect(self):
        if self._closing:
            return

        # Create a new connection
        self.connect()

    def run(self, callback=print):
        self.callback = self.callback or callback
        IOLoop.instance().add_timeout(5000, self.connect_or_exit)

    def connect_or_exit(self):
        try:
            self.connect()
        except Exception:
            sys.exit(1)
