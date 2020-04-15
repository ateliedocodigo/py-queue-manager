#!/usr/bin/env python
"""
.. code:: python

    consumer = PubsubConsumer('project_id', 'path/to/sa.json', 'subscription_name', 'topic_name')

    def callback(message):
        print("message", message)

    try:
        consumer.start_listening(callback)
    except KeyboardInterrupt:
        consumer.stop()
"""
from logging import getLogger

from . import QueueConsumer

try:
    import google
    from google.api_core.exceptions import GoogleAPICallError
    from google.cloud import pubsub
    from google.oauth2.service_account import Credentials
except ModuleNotFoundError:
    raise ModuleNotFoundError("You need to install google-cloud-pubsub")

logger = getLogger(__name__)


class PubsubConsumer(QueueConsumer):
    scope = 'https://www.googleapis.com/auth/pubsub'

    def __init__(self, project_id, service_account_file_path, subscription_name, topic_name):
        logger.info("Initializing PubSub consumer")
        self.project_id = project_id
        self.service_account_file_path = service_account_file_path
        self.subscription_name = subscription_name
        self.topic_name = topic_name
        self.client = self.setup_client()
        self.subscription_path = self.client.subscription_path(self.project_id, self.subscription_name)

    def on_message(self, message):
        try:
            self.callback(message.data)
        except Exception as e:
            logger.exception(f"ERROR! Couldn't process the following message: {message.data} {e}")
            message.nack()
        else:
            logger.info(f"Message acknowledged: {message.data}")
            message.ack()

    def setup_client(self):
        credentials = Credentials.from_service_account_file(
            self.service_account_file_path, scopes=(self.scope,)
        )
        return pubsub.SubscriberClient(credentials=credentials)

    def start_listening(self, callback=print):
        self.callback = callback
        logger.info("Trying to connect to PubSub ...")
        try:
            self.client.get_subscription(self.subscription_path)
        except google.api_core.exceptions.NotFound:
            logger.warning('Subscription (%s) DO NOT exits. App will try to create automatically.',
                           self.subscription_path)
            topic_path = self.client.topic_path(self.project_id, self.topic_name)
            self.client.create_subscription(self.subscription_path, topic_path)
            # create the subscription, if goes well continue, if not let the Exception throws
            logger.info('Subscription created successfully.')
        self.client.subscribe(self.subscription_path, self.on_message)
        logger.info("PubSub has connected successfully to the topic.")
        logger.info("Application is listening to the PubSub topic...")

    def is_connected(self):
        from warnings import warn
        warn('Deprecated, use ping instead', DeprecationWarning)
        return self.ping()

    def ping(self):
        try:
            self.client.get_subscription(self.subscription_path)
            return True
        except GoogleAPICallError:
            return False
