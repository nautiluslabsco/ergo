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
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channelx = connection.channel()
        queue_name = self._invocable.reference
        channelx.queue_declare(queue=queue_name)

        def handler(channel, method, properties, body) -> None:   # type: ignore
            data_out: Payload = Payload()
            data_in: Payload = Payload(dict(json.loads(body.decode('utf-8'))))

            self._invocable.invoke(data_out, data_in)

            channelx.basic_publish(exchange='primary', routing_key='a.b.c', body=str(data_out))

        channelx.basic_consume(queue=queue_name, auto_ack=True, on_message_callback=handler)

        channelx.start_consuming()

        return 0
