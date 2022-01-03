
Configuration
=============

Ergo tries to abstract away infrastructure related
code through the use of configuration files. Often
for more advanced usage the tool requires two types
of files:

- Namespaces_
- Configs_

Namespaces
----------
An execution environment, necessary information to run
the code in the specified infrastructure according to
a protocol Ergo can handle.

.. py:class:: namespace

   .. py:attribute:: protocol
        :type: str

        Execution protocol for this namespace. 
        May be ``http`` or ``amqp`` for example.


   .. py:attribute:: host
        :type: str

        Target host for this protocol.

An example namespace file, titled ``my_namespace.yaml``:

.. code-block:: python

   protocol: amqp
   host: amqps://guest:guest@localhost:5671


Configs
-------

Infrastructure related configuration specific to the service being run.
Specifies what function is being injected, what namespace is being used, etc.

.. py:class:: config

   .. py:attribute:: namespace
        :type: str

        Namespace file to use.

   .. py:attribute:: func
        :type: str

        Function (or generator) to inject.

   .. py:attribute:: subtopic
        :type: str

        Topic to subscribe to. Often protocol specific.

   .. py:attribute:: pubtopic
        :type: str

        Topic to publish to. Often protocol specific.

   .. py:attribute:: args
        :type: Dict

        Translation map for key-value pairs in payload to function arguments.

Imagine there is some business logic like so in ``my_func.py``:

.. code-block:: python

   def sum(x, y):
        return x + y 


An example config (``my_config.yaml``) might then look like:

.. code-block:: guess

   namespace: my_namespace.yaml
   func: my_func.py:sum
   subtopic: num
   pubtopic: sum

