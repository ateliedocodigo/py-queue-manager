import logging

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import pubsub_v1
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class PubsubPublisher:
    scope = 'https://www.googleapis.com/auth/pubsub'

    def __init__(self, project_id, service_account_file_path, topic_name="ping"):
        logger.debug('Init PubSubManager ...')
        self.project_id = project_id
        self.service_account_file_path = service_account_file_path

        full_topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=self.project_id,
            topic=topic_name,
        )
        topic_name_ping = 'projects/{project_id}/topics/ping'.format(
            project_id=self.project_id,
        )

        self.full_topic_name = full_topic_name
        self.topic_name_ping = topic_name_ping

    def assert_topic(self, topic_name):
        try:
            self.client = self.get_pubsub_client()
            self.client.get_topic(topic_name)
        except GoogleAPICallError as error:
            if error.code == 404:
                logger.info('Topic doesnt exist, creating a new topic {}'.format(topic_name))
                self.client.create_topic(topic_name)
            else:
                logger.error('An error occurred while getting the topic {topic_name}, reason: {error}'.format(
                    topic_name=topic_name,
                    error=error
                ))
                raise error

    def get_pubsub_client(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file_path,
            scopes=(self.scope,)
        )
        publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
        return publisher_client

    def ping(self):
        self.assert_topic(self.topic_name_ping)
        response = self.client.publish(topic=self.topic_name_ping, data=b"OK")
        message_id = response.result(timeout=5000)
        logger.debug(f"Response from PubSub: {message_id}")
        return message_id

    def send_message(self, payload):
        from warnings import warn
        warn('Deprecated, use publish_message instead', DeprecationWarning)
        return self.publish_message(payload)

    def publish_message(self, message):
        if type(message) is not bytes:
            message = message.encode('utf-8')
        self.assert_topic(self.full_topic_name)
        response = self.client.publish(self.full_topic_name, message)
        return response.result(timeout=5000)
