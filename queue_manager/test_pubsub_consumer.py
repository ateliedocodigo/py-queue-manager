from unittest import TestCase, skipIf
from unittest.mock import patch, Mock

try:
    from .pubsub_consumer import PubsubConsumer
except ModuleNotFoundError:
    pubsub_installed = False
else:
    pubsub_installed = True


@skipIf(not pubsub_installed, "Skipping cause google-cloud-pubsub is not installed")
class TestPubsubConsumer(TestCase):

    @patch("queue_manager.pubsub_consumer.Credentials", Mock())
    def test_should_initialize(self):
        self.assertIsInstance(PubsubConsumer(None, None, None, None), PubsubConsumer)
