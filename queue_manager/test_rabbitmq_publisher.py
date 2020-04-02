from unittest import TestCase, skipIf

try:
    from .rabbitmq_publisher import RabbitMqPublisher
except ModuleNotFoundError:
    pika_installed = False
else:
    pika_installed = True


@skipIf(not pika_installed, "Skipping cause pika is not installed")
class TestRabbitMqPublisher(TestCase):

    def test_should_initialize(self):
        self.assertIsInstance(RabbitMqPublisher(''), RabbitMqPublisher)
