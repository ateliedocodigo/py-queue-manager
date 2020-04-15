from unittest import TestCase, skipIf
from unittest.mock import patch, Mock

try:
    from .pubsub_publisher import PubsubPublisher
except ModuleNotFoundError:
    pubsub_installed = False
else:
    pubsub_installed = True


@skipIf(not pubsub_installed, "Skipping cause google-cloud-pubsub is not installed")
class TestPubsubPublisher(TestCase):

    @patch("queue_manager.pubsub_publisher.Credentials", Mock())
    def test_should_initialize(self):
        self.assertIsInstance(PubsubPublisher(None, None, None), PubsubPublisher)
