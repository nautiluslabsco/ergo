"""Summary."""
import logging
import signal

import socket
import threading
import time
from contextlib import contextmanager
from typing import Callable, Dict
from urllib.parse import urlparse

import amqp.exceptions
import kombu
import kombu.exceptions
import kombu.message
from kombu.pools import connections, producers

from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.message import Message, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import extract_from_stack, instance_id

# content_type: application/json
# {"x":5,"y":7}

logging.getLogger("amqp.connection.Connection.heartbeat_tick").setLevel(logging.DEBUG)

CONSUMER_PREFETCH_COUNT = 2


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

        self._terminating = threading.Event()
        self._active_handlers = threading.Semaphore()

    def start(self) -> int:
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        while not self._terminating.is_set():
            try:
                with self.new_connection() as conn:
                    print("new connection")
                    consumer: kombu.Consumer = conn.Consumer(queues=[self.component_queue, self.instance_queue], prefetch_count=CONSUMER_PREFETCH_COUNT)
                    consumer.register_callback(self.handle_message)
                    with consumer:
                        while not self._terminating.is_set():
                            try:
                                conn.drain_events(timeout=1)
                            except socket.timeout:
                                conn.heartbeat_check()
            except OSError:
                pass
            except (kombu.exceptions.ConnectionError, kombu.exceptions.OperationalError, amqp.exceptions.RecoverableConnectionError):
                time.sleep(1)
        return 0

    def handle_message(self, body, message: kombu.message.Message):
        threading.Thread(target=self.handle_message_inner, args=(body, message.ack)).start()

    def handle_message_inner(self, body, ack: Callable):
        message_in = decodes(body)
        self._active_handlers.acquire(blocking=False)
        try:
            for message_out in self.invoke_handler(message_in):
                routing_key = str(PubTopic(message_out.key))
                self.publish(message_out, routing_key)
        except Exception as err:  # pylint: disable=broad-except
            message_in.error = make_error_output(err)
            message_in.traceback = str(err)
            self.publish(message_in, self.error_queue_name)
        finally:
            ack()
            self._active_handlers.release()

    def publish(self, ergo_message: Message, routing_key: str):
        amqp_message = encodes(ergo_message)
        with self.new_producer() as producer:
            ensured_publish = producer.connection.ensure(producer, producer.publish)
            ensured_publish(
                amqp_message,
                exchange=self.exchange,
                routing_key=routing_key,
                declare=[self.error_queue],
            )

    @contextmanager
    def new_connection(self) -> kombu.Connection:
        with connections[self.connection].acquire(block=True) as conn:
            yield conn

    @contextmanager
    def new_producer(self) -> kombu.Producer:
        with producers[self.connection].acquire(block=True) as conn:
            yield conn

    def _sigterm_handler(self, *args):
        self._terminating.set()
        self._active_handlers.acquire()
        signal.signal(signal.SIGTERM, 0)
        signal.raise_signal(signal.SIGTERM)
