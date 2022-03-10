"""Summary."""
import logging
import signal

import socket
import threading
import time
import traceback
from contextlib import contextmanager
from typing import Callable, Dict
from urllib.parse import urlparse

import amqp.exceptions
import kombu
import kombu.exceptions
import kombu.message
from kombu.pools import producers

from ergo.util import defer_termination
from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.message import Message, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import extract_from_stack, instance_id

# content_type: application/json
# {"x":5,"y":7}

logger = logging.getLogger(__name__)
logging.getLogger("amqp.connection.Connection.heartbeat_tick").setLevel(logging.DEBUG)

CONSUMER_PREFETCH_COUNT = 5
TERMINATION_GRACE_PERIOD = 60  # seconds


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
        self.exchange = kombu.Exchange(name=self._invocable.config.exchange, type="topic", durable=True, auto_delete=False)

        component_queue_name = f"{self._invocable.config.func}".replace("/", ":")
        if component_queue_name.startswith(":"):
            component_queue_name = component_queue_name[1:]
        self.component_queue = kombu.Queue(name=component_queue_name, exchange=self.exchange, routing_key=str(SubTopic(self._invocable.config.subtopic)), durable=False)
        instance_queue_name = f"{component_queue_name}:{instance_id()}"
        self.instance_queue = kombu.Queue(name=instance_queue_name, exchange=self.exchange, routing_key=str(SubTopic(instance_id())), auto_delete=True)
        error_queue_name = f"{component_queue_name}:error"
        self.error_queue = kombu.Queue(name=error_queue_name, exchange=self.exchange, routing_key=str(SubTopic(error_queue_name)), durable=False)

        self.consumer: kombu.Consumer = self.connection.Consumer(queues=[self.component_queue, self.instance_queue], prefetch_count=CONSUMER_PREFETCH_COUNT)
        self.consumer.register_callback(self.handle_message)

        self._terminating = threading.Event()
        self._active_handlers = threading.Semaphore()
        self._handler_lock = threading.Lock()

    def start(self) -> int:
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        with self.connection:
            conn = self.connection
            while not self._terminating.is_set():
                self.consumer.consume()
                try:
                    conn.drain_events(timeout=1)
                except socket.timeout:
                    conn.heartbeat_check()
                except conn.connection_errors:
                    logger.warning("connection closed. reviving.")
                    conn = self.connection.clone()
                    conn.ensure_connection()
                    self.consumer.revive(conn.channel())
        return 0

    def handle_message(self, body, message: kombu.message.Message):
        self._active_handlers.acquire(blocking=False)
        threading.Thread(target=self.handle_message_inner, args=(body, message.ack)).start()

    def handle_message_inner(self, body, ack: Callable):
        with self._handler_lock:
            message_in = decodes(body)
            try:
                for message_out in self.invoke_handler(message_in):
                    routing_key = str(PubTopic(message_out.key))
                    self.publish(message_out, routing_key)
            except Exception as err:  # pylint: disable=broad-except
                message_in.error = make_error_output(err)
                message_in.traceback = str(err)
                self.publish(message_in, self.error_queue.name)
            finally:
                # TODO figure out why this sometimes raises amqp.exceptions.RecoverableConnectionError on SIGTERM
                ack()
                self._active_handlers.release()

    def publish(self, ergo_message: Message, routing_key: str):
        amqp_message = encodes(ergo_message).encode("utf-8")
        with self.producer() as producer:
            producer.publish(
                amqp_message,
                content_encoding="binary",
                exchange=self.exchange,
                routing_key=routing_key,
                retry=True,
                declare=[self.component_queue, self.instance_queue, self.error_queue],
            )

    @contextmanager
    def producer(self) -> kombu.Producer:
        with producers[self.connection].acquire(block=True) as conn:
            yield conn

    def sigterm_handler(self, *args):
        self._terminating.set()
        self._active_handlers.acquire(blocking=True, timeout=TERMINATION_GRACE_PERIOD)
