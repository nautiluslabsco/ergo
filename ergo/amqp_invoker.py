"""Summary."""
import datetime
import logging
import signal
import socket
import threading
from contextlib import contextmanager
from typing import Callable, Dict
from urllib.parse import urlparse

import kombu
import kombu.exceptions
import kombu.message
from kombu.pools import producers

from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.message import Message, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import extract_from_stack, instance_id

logger = logging.getLogger(__name__)

PREFETCH_COUNT = 1
TERMINATION_GRACE_PERIOD = 60  # seconds
# rabbitmq's recommended default https://www.rabbitmq.com/heartbeats.html#heartbeats-timeout
DEFAULT_HEARTBEAT = 60  # seconds.


def set_param(host: str, param_key: str, param_val: str) -> str:
    """Overwrite a param in a host string w a new value."""
    uri, new_param = urlparse(host), f'{param_key}={param_val}'
    params = [p for p in uri.query.split('&') if param_key not in p] + [new_param]
    return uri._replace(query='&'.join(params)).geturl()


def make_error_output(err: Exception) -> Dict[str, str]:
    """Make a more digestible error output."""
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

        heartbeat = self._invocable.config.heartbeat or DEFAULT_HEARTBEAT
        self._connection = kombu.Connection(self._invocable.config.host, heartbeat=heartbeat)
        self._exchange = kombu.Exchange(name=self._invocable.config.exchange, type="topic", durable=True, auto_delete=False)

        component_queue_name = f"{self._invocable.config.func}".replace("/", ":")
        if component_queue_name.startswith(":"):
            component_queue_name = component_queue_name[1:]
        self._component_queue = kombu.Queue(name=component_queue_name, exchange=self._exchange, routing_key=str(SubTopic(self._invocable.config.subtopic)), durable=False)
        instance_queue_name = f"{component_queue_name}:{instance_id()}"
        self._instance_queue = kombu.Queue(name=instance_queue_name, exchange=self._exchange, routing_key=str(SubTopic(instance_id())), auto_delete=True)
        error_queue_name = f"{component_queue_name}:error"
        self._error_queue = kombu.Queue(name=error_queue_name, exchange=self._exchange, routing_key=error_queue_name, durable=False)

        self._terminating = threading.Event()
        self._pending_invocations = threading.Semaphore()
        self._handler_lock = threading.Lock()

    def start(self) -> int:
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)
        with self._connection:
            conn = self._connection
            consumer: kombu.Consumer = conn.Consumer(queues=[self._component_queue, self._instance_queue], prefetch_count=PREFETCH_COUNT)
            consumer.register_callback(self._start_handle_message_thread)
            consumer.consume()
            while not self._terminating.is_set():
                try:
                    # wait up to 1s for the next message before sending a heartbeat
                    conn.drain_events(timeout=1)
                except socket.timeout:
                    conn.heartbeat_check()
                except conn.recoverable_connection_errors:
                    logger.warning("connection closed. reviving.")
                    conn = self._connection.clone()
                    conn.ensure_connection()
                    consumer.revive(conn.channel())
                    consumer.consume()
        return 0

    def _start_handle_message_thread(self, body: str, message: kombu.message.Message):
        # _handle_sigterm will wait for _handle_message to release this semaphore
        self._pending_invocations.acquire(blocking=False)
        threading.Thread(target=self._handle_message, args=(body, message.ack)).start()

    def _handle_message(self, body: str, ack: Callable):
        # there may be up to PREFETCH_COUNT _handle_message threads alive at a time, but we want them to execute
        # sequentially to guarantee that messages are acknowledged in the order they're received
        with self._handler_lock:
            ergo_message = decodes(body)
            try:
                self._handle_message_inner(ergo_message)
            finally:
                ack()
                self._pending_invocations.release()

    def _handle_message_inner(self, message_in: Message):
        try:
            for message_out in self.invoke_handler(message_in):
                routing_key = str(PubTopic(message_out.key))
                self._publish(message_out, routing_key)
        except Exception as err:  # pylint: disable=broad-except
            dt = datetime.datetime.now(datetime.timezone.utc)
            message_in.error = make_error_output(err)
            message_in.traceback = str(err)
            message_in.scope.metadata['timestamp'] = dt.isoformat()
            self._publish(message_in, self._error_queue.name)

    def _publish(self, ergo_message: Message, routing_key: str):
        amqp_message = encodes(ergo_message).encode("utf-8")
        with self._producer() as producer:
            producer.publish(
                amqp_message,
                content_encoding="binary",
                exchange=self._exchange,
                routing_key=routing_key,
                retry=True,
                declare=[self._instance_queue, self._error_queue],
            )

    @contextmanager
    def _producer(self) -> kombu.Producer:
        with producers[self._connection].acquire(block=True) as conn:
            yield conn

    def _handle_sigterm(self, signum, *_):
        self._terminating.set()
        self._pending_invocations.acquire(blocking=True, timeout=TERMINATION_GRACE_PERIOD)
        self._connection.close()
        signal.signal(signal.SIGTERM, 0)
        signal.raise_signal(signum)
