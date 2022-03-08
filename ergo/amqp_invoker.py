"""Summary."""
import asyncio
import kombu
import kombu.message
import socket
from kombu.pools import producers, connections
from typing import Iterable, Dict, cast
from urllib.parse import urlparse

import aio_pika
import aiomisc
import jsons
from retry import retry

from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.message import Message, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import defer_termination, extract_from_stack, instance_id

# content_type: application/json
# {"x":5,"y":7}

MAX_THREADS = 4
CHANNEL_POOL_SIZE = 2  # minimum is 1 per active run_queue_loop coroutine


def set_param(host: str, param_key: str, param_val: str) -> str:
    """Overwrite a param in a host string w a new value."""
    uri, new_param = urlparse(host), f'{param_key}={param_val}'
    params = [p for p in uri.query.split('&') if param_key not in p] + [new_param]
    return uri._replace(query='&'.join(params)).geturl()


def make_error_output(err: Exception) -> Dict[str, str]:
    """Make a more digestable error output."""
    orig = err.__context__ or err
    err_output = {
        'type': type(orig).__name__,
        'message': str(orig),
    }
    filename, lineno, function_name = extract_from_stack(orig)
    if None not in (filename, lineno, function_name):
        err_output = {**err_output, 'file': filename, 'line': lineno, 'func': function_name}
    return err_output


class AmqpInvoker(Invoker):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        super().__init__(invocable)

        host = self._invocable.config.host
        heartbeat = self._invocable.config.heartbeat

        self.url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host
        self.connection = kombu.Connection(self.url)
        self.exchange_name = self._invocable.config.exchange
        self.exchange = kombu.Exchange(name=self.exchange_name, type="topic", durable=True, auto_delete=False)
        self.component_queue_name = f"{self._invocable.config.func}".replace("/", ":")
        if self.component_queue_name.startswith(":"):
            self.component_queue_name = self.component_queue_name[1:]
        self.component_queue = kombu.Queue(name=self.component_queue_name, exchange=self.exchange, routing_key=str(SubTopic(self._invocable.config.subtopic)), durable=False)
        self.instance_queue_name = f"{self.component_queue_name}:{instance_id()}"
        self.instance_queue = kombu.Queue(name=self.instance_queue_name, exchange=self.exchange, routing_key=str(SubTopic(instance_id())), auto_delete=True)
        self.error_queue_name = f"{self.component_queue_name}:error"
        self.error_queue = kombu.Queue(name=self.error_queue_name, exchange=self.exchange, routing_key=str(SubTopic(self.error_queue_name)), durable=False)

    def start(self):
        with connections[self.connection].acquire(block=True) as conn:
            conn = cast(kombu.Connection, conn)
            consumer: kombu.Consumer = conn.Consumer(queues=[self.component_queue, self.instance_queue])
            consumer.register_callback(self.handle_message)
            with consumer:
                while True:
                    conn.drain_events()
                    try:
                        conn.drain_events(timeout=1)
                    except socket.timeout:
                        conn.heartbeat_check()

    def handle_message(self, body, amqp_message: kombu.message.Message):
        with defer_termination():
            ergo_message = decodes(body)
            try:
                self.handle_message_inner(ergo_message)
            finally:
                amqp_message.ack()

    def handle_message_inner(self, message_in: Message):
        try:
            for message_out in self.do_work(message_in):
                message = encodes(message_out).encode('utf-8')
                routing_key = str(PubTopic(message_out.key))
                self.publish(message, routing_key)
        except Exception as err:  # pylint: disable=broad-except
            message_in.error = make_error_output(err)
            message_in.traceback = str(err)
            message = jsons.dumps(message_in).encode('utf-8')
            self.publish(message, self.error_queue_name)

    def publish(self, message, routing_key: str):
        with producers[self.connection].acquire(block=True) as producer:
            producer.publish(
                message,
                exchange=self.exchange,
                routing_key=routing_key,
                declare=[self.error_queue],
            )

    # @aiomisc.threaded_iterable_separate
    def do_work(self, data_in: Message) -> Iterable[Message]:
        """
        Performs the potentially long-running work of `self._invocable.invoke` in a separate thread
        within the constraints of the underlying execution context.

        Parameters:
            data_in: Raw event data

        Yields:
            message: Lazily-evaluable wrapper around return values from `self._invocable.invoke`, plus metadata
        """
        yield from self.invoke_handler(data_in)
