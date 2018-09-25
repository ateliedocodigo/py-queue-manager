CHANGELOG
=========

1.5.0
-----

* Supports multiple hosts on `QueueManager` (requires pika's master branch) [See pika#528](https://github.com/pika/pika/issues/528)


1.4.0
-----

* Supports multiple hosts on `RabbitMqConsumer` (requires pika's master branch) [See pika#528](https://github.com/pika/pika/issues/528)

1.3.0
-----

* Add dynamic queue declaration on consume exchange
* Add reject message on exception

1.2.0
-----

* Add exchange support on `RabbitMqConsumer`

1.1.0
-----

* Add ping to QueueManager
* Move queue_args to specific methods

1.0.0
-----

* Initial release
