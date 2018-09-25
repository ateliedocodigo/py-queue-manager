py-queue-manager
================

Library to deal with RabbitMQ

Usage
-----

QueueManager class
..................

.. code:: python

    >>> from queue_manager import QueueManager
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

Inspired on: asynchronous_publisher_example_

.. code:: python

    from queue_manager import RabbitMqPublisher

    producer = RabbitMqPublisher('amqp://username:password@hostname:port',
                                 'exchange', 'exchange_type', 'queue_name', 'routing_key')

    producer.run()

    producer.publish_message('hello')

    producer.stop()


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


Running tests with ``tox``
--------------------------

Install ``tox``

::

    $ pip install tox

Run tests

::

    tox


.. _asynchronous_publisher_example: http://pika.readthedocs.io/en/0.10.0/examples/asynchronous_publisher_example.html

.. _asynchronous_consumer_example: http://pika.readthedocs.io/en/0.10.0/examples/asynchronous_consumer_example.html
