from unittest import TestCase, skipIf

try:
    from .queue_manager import QueueManager
except ModuleNotFoundError:
    pika_installed = False
else:
    pika_installed = True


@skipIf(not pika_installed, "Skipping cause pika is not installed")
class TestQueueManager(TestCase):

    def test_should_initialize(self):
        self.assertIsInstance(QueueManager({}), QueueManager)
