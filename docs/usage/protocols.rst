
Protocols
=========

AMQP
----

The `AMQP <https://www.rabbitmq.com/tutorials/amqp-concepts.html>`_ Protocol is
a messaging protocol supported by message brokers like RabbitMQ.

When run using the ``amqp`` protocol, Ergo will:

- create a queue using the function name in the given ``exchange``
- create a binding for this queue based on the ``subtopic``
- publish outbound messages against ``pubtopic``
- translate incoming message fields to function arguments based on ``args``

Payload translation happens as follows:
Ergo matches based on keywords. So if an incoming message looks like:

.. code-block:: guess

   {"data": {"x": 2, "y": 3}}

and the injected function looks like:

.. code-block:: python

   def my_sum(data):
        return data['x'] + data['y']

then the data dictionary will be passed along perfectly fine!

However, if your function looks like either of the following:

.. code-block:: python

   def my_sum(event):
        return event['x'] + event['y']

or,

.. code-block:: python

   def my_sum(x, y):
        return x + y


Then payload -> parameters translation will fail. To get around this,
Ergo allows developers to specify translation maps. For example, in ``my_config.yaml``
you can specify the following:

.. code-block:: guess 

   ...
   args:
        event: data
   ...

or,

.. code-block:: guess

   ...
   args:
        x: data.x
        y: data.y
   ...

This additionally gives flexibility to rename parameters. For example you could also do the following:

.. code-block:: guess

   ...
   args:
        a: data.x
        b: data.y
   ...

.. code-block:: python

   def my_sum(a, b):
        return a + b


And Ergo will translate the payloads fields to the function signature!
