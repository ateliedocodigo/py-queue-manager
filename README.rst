py-queue-manager
================

Library to deal with RabbitMQ

Usage
-----

QueueManager class
..................

.. code:: python

    >>> from queue_manager.queue_manager import QueueManager
    >>> conn_params = {
    ...     'host': '',
    ...     'port': '',
    ...     'username': '',
    ...     'password': ''
    ... }
    >>> # or use multiple urls
    >>> conn_params = ('amqp://host1', 'amqp://host2',)
    qm = QueueManager(conn_params)
    >>> qm.push('hello', 'Hello from QueueManager')
    True
    >>> qm.pop('hello')
    Hello from QueueManager
    >>> del(qm)

RabbitMqPublisher class
.......................

.. code:: python

    from queue_manager.rabbitmq_consumer import RabbitMqPublisher

    producer = RabbitMqPublisher('amqp://username:password@hostname:port',
                                 'exchange', 'exchange_type', 'queue_name', 'routing_key')

    producer.publish_message('hello')
    # or passing message property
    producer.publish_message('hello', dict(priority=8))


RabbitMqConsumer class
......................

This class is an async consumer class, that still connected.

Inspired on: asynchronous_consumer_example_

.. code:: python

    single_url = 'amqp://username:password@hostname:port'
    # or multiple urls
    multiple_urls = ('amqp://username:password@hostnameone:port', 'amqp://username:password@hostnametwo:port')
    consumer = RabbitMqConsumer(single_url, queue='queue_name')

    try:
        def callback(body):
            print("message body", body)

        consumer.run(callback)
    except KeyboardInterrupt:
        consumer.stop()

TornadoConsumer class
.......................

.. code:: python

    from tornado.ioloop import IOLoop
    from queue_manager.tornado_consumer import TornadoConsumer

    consumer = TornadoConsumer('amqp://username:password@hostname:port',
                               'exchange', 'exchange_type', 'queue_name', 'routing_key')


    def callback(body):
        print("message body", body)

    consumer.run(callback)
    IOLoop.instance().start()

PubsubConsumer class
.......................

.. code:: python

    consumer = PubsubConsumer('project_id', 'path/to/sa.json', 'subscription_name', 'topic_name')

    def callback(message):
        print("message", message)

    try:
        consumer.start_listening(callback)
    except KeyboardInterrupt:
        consumer.stop()

Running tests with ``tox``
--------------------------

Install ``tox``

::

    $ pip install tox

Run tests

::

    tox

.. _asynchronous_consumer_example: http://pika.readthedocs.io/en/0.13.1/examples/asynchronous_consumer_example.html
