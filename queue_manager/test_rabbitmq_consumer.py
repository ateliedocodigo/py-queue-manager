from unittest import TestCase, skipIf

try:
    from .rabbitmq_consumer import RabbitMqConsumer
except ModuleNotFoundError:
    pika_installed = False
else:
    pika_installed = True


@skipIf(not pika_installed, "Skipping cause pika is not installed")
class TestRabbitMqConsumer(TestCase):

    def test_should_initialize(self):
        self.assertIsInstance(RabbitMqConsumer(''), RabbitMqConsumer)
