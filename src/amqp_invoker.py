"""Summary."""
import json
import threading
from typing import Any, List, Tuple
from urllib.parse import urlparse
from markupsafe import functools
import pika
from src.function_invocable import FunctionInvocable
from src.invoker import Invoker
from src.types import TYPE_PAYLOAD

# content_type: application/json
# {"x":5,"y":7}


def set_param(host: str, param_key: str, param_val: str) -> str:
    """Overwrite a param in a host string w a new value."""
    uri, new_param = urlparse(host), f'{param_key}={param_val}'
    params = [p for p in uri.query.split('&') if param_key not in p] + [new_param]
    return uri._replace(query='&'.join(params)).geturl()


class AmqpInvoker(Invoker):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        super().__init__(invocable)
        self.threads: List[threading.Thread] = []

    def start(self) -> int:
        """Summary."""
        connection, channel, queue_name, queue_name_error = self.connect()
        wrapper = functools.partial(self.on_message, args=(connection, self.threads, queue_name_error))
        channel.basic_consume(queue=queue_name, auto_ack=True, on_message_callback=wrapper)
        channel.start_consuming()
        return 0

    def connect(self) -> Tuple[pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel, str, str]:
        """Connect to a rabbit broker."""
        heartbeat = self._invocable.config.heartbeat
        host = set_param(self._invocable.config.host, 'heartbeat', str(heartbeat)) if heartbeat else self._invocable.config.host
        parameters = pika.URLParameters(host)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        queue_name = self._invocable.config.func
        queue_name_error = f'{queue_name}_error'
        exchange_name = self._invocable.config.exchange
        channel.queue_declare(queue=queue_name)
        channel.queue_declare(queue=queue_name_error)
        channel.exchange_declare(exchange_name, exchange_type='topic', passive=False, durable=True, auto_delete=False, internal=False, arguments=None)
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=str(self._invocable.config.subtopic))
        return connection, channel, queue_name, queue_name_error

    def on_message(self, channel, method, properties, body, args) -> None:  # type: ignore
        connection, threads, routing_key = args
        t = threading.Thread(target=self.do_work, args=(connection, channel, body, method.delivery_tag, routing_key))
        t.start()
        threads.append(t)

    def do_work(self, connection, channel, body, delivery_tag, routing_key) -> None:  # type: ignore
        # thread_id = threading.get_ident()
        # TODO: can be used for tracing

        # Perform actual work
        data_in: TYPE_PAYLOAD = dict(json.loads(body.decode('utf-8')))
        try:
            for data_out in self._invocable.invoke(data_in["data"]):
                payload = {
                    "data": data_out,
                    "key": str(self._invocable.config.pubtopic),
                    "log": data_in.get("log", []),
                }
                channel.basic_publish(exchange=self._invocable.config.exchange,
                                      routing_key=str(self._invocable.config.pubtopic), body=json.dumps(payload))
        except Exception as err:  # pylint: disable=broad-except
            data_in['error'] = str(err)
            channel.basic_publish(exchange='', routing_key=routing_key, body=json.dumps(data_in))

        callback = functools.partial(self.ack, channel, delivery_tag)
        connection.add_callback_threadsafe(callback)

    def ack(self, channel, delivery_tag) -> None:  # type: ignore
        if channel.is_open:
            channel.basic_ack(delivery_tag)
        else:
            # TODO: can log or raise exception
            pass
