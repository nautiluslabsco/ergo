"""Summary."""
import json

import pika

from src.invoker import Invoker
from src.types import TYPE_PAYLOAD

# content_type: application/json
# {"x":5,"y":7}


class AmqpInvoker(Invoker):
    """Summary."""

    def start(self) -> int:
        """Summary."""
        parameters = pika.URLParameters(self._invocable.config.host)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        queue_name = self._invocable.config.func
        queue_name_error = f'{queue_name}_error'
        exchange_name = self._invocable.config.exchange
        channel.queue_declare(queue=queue_name)
        channel.queue_declare(queue=queue_name_error)
        channel.exchange_declare(exchange_name, exchange_type='topic', passive=False, durable=True, auto_delete=False, internal=False, arguments=None)

        channel.queue_bind(exchange=self._invocable.config.exchange, queue=queue_name, routing_key=str(self._invocable.config.subtopic))

        def handler(channel, method, properties, body) -> None:  # type: ignore
            """Summary.

            Args:
                channel (TYPE): Description
                method (TYPE): Description
                properties (TYPE): Description
                body (TYPE): Description
            """
            data_in: TYPE_PAYLOAD = dict(json.loads(body.decode('utf-8')))
            data_in['key'] = str(self._invocable.config.subtopic)
            try:
                for data_out in self._invocable.invoke(data_in):
                    data_out['key'] = str(self._invocable.config.pubtopic)
                    channel.basic_publish(exchange=self._invocable.config.exchange, routing_key=str(self._invocable.config.pubtopic), body=json.dumps(data_out))
            except Exception as err:  # pylint: disable=broad-except
                data_in['error'] = str(err)
                channel.basic_publish(exchange='', routing_key=queue_name_error, body=json.dumps(data_in))

        channel.basic_consume(queue=queue_name, auto_ack=True, on_message_callback=handler)

        channel.start_consuming()

        return 0
