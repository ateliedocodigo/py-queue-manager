from abc import ABCMeta


class QueuePublisher(metaclass=ABCMeta):
    def ping(self) -> bool:
        raise NotImplementedError()

    def publish_message(self, message, message_properties=None):
        raise NotImplementedError()


class QueueConsumer(metaclass=ABCMeta):
    def ping(self) -> bool:
        raise NotImplementedError()

    def start_listening(self, callback=None):
        raise NotImplementedError()
