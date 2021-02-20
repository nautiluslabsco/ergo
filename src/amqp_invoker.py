"""Summary."""
import json

import pika

from src.invoker import Invoker
from src.payload import Payload

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
        channel.queue_declare(queue=queue_name)
        channel.exchange_declare(self._invocable.config.exchange, exchange_type='topic', passive=False, durable=True, auto_delete=False, internal=False, arguments=None)

        channel.queue_bind(exchange=self._invocable.config.exchange, queue=queue_name, routing_key=str(self._invocable.config.subtopic))

        def handler(channel, method, properties, body) -> None:  # type: ignore
            """Summary.

            Args:
                channel (TYPE): Description
                method (TYPE): Description
                properties (TYPE): Description
                body (TYPE): Description
            """
            data_in: Payload = Payload(dict(json.loads(body.decode('utf-8'))))
            for data_out in self._invocable.invoke(data_in):
                channel.basic_publish(exchange=self._invocable.config.exchange, routing_key=str(self._invocable.config.pubtopic), body=str(data_out))

        channel.basic_consume(queue=queue_name, auto_ack=True, on_message_callback=handler)

        channel.start_consuming()

        return 0
