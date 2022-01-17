import json
from test.integration.utils import Component, retries
from typing import Callable, Dict, Optional, TypeVar

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

try:
    from collections.abc import Generator
except ImportError:
    from typing import Generator

from collections import defaultdict

from ergo.topic import PubTopic

AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "amq.topic"  # use a pre-declared exchange that we kind bind to while the ergo runtime is booting
SHORT_TIMEOUT = 0.01
_LIVE_COMPONENTS: Dict = defaultdict(int)


AMQPComponentType = TypeVar('AMQPComponentType', bound='AMQPComponent')


class AMQPComponent(Component):
    protocol = "amqp"
    host = AMQP_HOST

    def __init__(self, func: Callable, subtopic: Optional[str]=None, pubtopic: Optional[str]=None):
        super().__init__(func)
        self.subtopic = subtopic or f"{self.queue}_sub"
        self.pubtopic = pubtopic or f"{self.queue}_pub"
        self.channel = new_channel()
        self._subscription_queue = self.channel.queue_declare(
            queue="",
            exclusive=True,
        ).method.queue
        self.channel.queue_bind(self._subscription_queue, EXCHANGE, routing_key=str(self.pubtopic))

    @property
    def namespace(self):
        ns = super().namespace
        ns["exchange"] = EXCHANGE
        ns["subtopic"] = self.subtopic
        if self.pubtopic:
            ns["pubtopic"] = self.pubtopic
        return ns

    def rpc(self, payload: Dict, inactivity_timeout=None):
        self.send(payload)
        return self.consume(inactivity_timeout=inactivity_timeout)

    def send(self, payload: Dict):
        publish(str(PubTopic(self.subtopic)), payload, channel=self.channel, exchange=EXCHANGE)

    def consume(self, inactivity_timeout=5):
        attempt = 0
        while True:
            value = consume(self._subscription_queue, channel=self.channel, inactivity_timeout=SHORT_TIMEOUT)
            if value:
                return value
            self.propagate_error(inactivity_timeout=SHORT_TIMEOUT)
            attempt += 1
            if inactivity_timeout and attempt >= inactivity_timeout * 20:
                return None

    def propagate_error(self, inactivity_timeout=None):
        body = consume(self.error_queue, inactivity_timeout=inactivity_timeout)
        if body:
            raise ComponentFailure(body["traceback"])

    def await_startup(self):
        for retry in retries(200, SHORT_TIMEOUT, pika.exceptions.ChannelClosedByBroker):
            with retry():
                channel = new_channel()
                channel.queue_declare(self.queue, passive=True)
        purge_queue(self.error_queue)
        purge_queue(self.queue)

    def __enter__(self) -> AMQPComponentType:
        super().__enter__()
        if not _LIVE_COMPONENTS[self.func]:
            self.await_startup()
        _LIVE_COMPONENTS[self.func] += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _LIVE_COMPONENTS[self.func] -= 1
        super().__exit__(exc_type, exc_val, exc_tb)


def publish(routing_key, payload, channel, exchange):
    channel.confirm_delivery()
    for retry in retries(200, SHORT_TIMEOUT, pika.exceptions.UnroutableError):
        with retry():
            body = json.dumps(payload).encode()
            channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body, mandatory=True)


def subscribe(routing_key, inactivity_timeout=None):
    channel = new_channel()
    queue_name = channel.queue_declare(
        queue="",
        auto_delete=True,
    ).method.queue
    channel.queue_bind(queue_name, EXCHANGE, routing_key=routing_key)

    return consume(queue_name, inactivity_timeout=inactivity_timeout, channel=channel)


def consume(queue_name, inactivity_timeout=None, channel=None):
    channel = channel or new_channel()
    method, _, body = next(channel.consume(queue_name, inactivity_timeout=inactivity_timeout))
    if body:
        channel.basic_ack(method.delivery_tag)
        return json.loads(body)
    return None


def purge_queue(queue_name: str):
    channel = new_channel()
    try:
        channel.queue_purge(queue_name)
    except pika.exceptions.ChannelClosedByBroker as exc:
        if "no queue" not in str(exc):
            raise


def new_channel() -> BlockingChannel:
    connection = pika.BlockingConnection(pika.URLParameters(AMQP_HOST))
    return connection.channel()


class ComponentFailure(BaseException):
    pass
