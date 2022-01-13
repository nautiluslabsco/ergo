import json
import pika
import pika.exceptions
from ergo.topic import SubTopic
from pika.adapters.blocking_connection import BlockingChannel
from test.integration.utils import Component, retries
from typing import Iterator, Callable, Optional, Dict
try:
    from collections.abc import Generator
except ImportError:
    from typing import Generator
from ergo.topic import PubTopic
from collections import defaultdict
import uuid

AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "amq.topic"  # use a pre-declared exchange that we kind bind to while the ergo runtime is booting
SHORT_TIMEOUT = 0.01
_LIVE_COMPONENTS: Dict = defaultdict(int)


class AMQPComponent(Component):
    protocol = "amqp"
    host = AMQP_HOST

    def __init__(self, func: Callable, subtopic: Optional[str]=None, pubtopic: Optional[str]=None):
        super().__init__(func)
        random_id = str(uuid.uuid4())
        self.subtopic = subtopic or f"{func.__name__}_{random_id}_sub"
        self.pubtopic = pubtopic or f"{func.__name__}_{random_id}_pub"
        self.channel = new_channel()

    @property
    def namespace(self):
        ns = super().namespace
        ns["exchange"] = EXCHANGE
        ns["subtopic"] = self.subtopic
        if self.pubtopic:
            ns["pubtopic"] = self.pubtopic
        return ns

    def rpc(self, payload: Dict, inactivity_timeout=None):
        subscription = self.new_subscription(inactivity_timeout=inactivity_timeout)
        self.send(payload)
        yield from subscription

    def send(self, payload: Dict):
        publish(str(PubTopic(self.subtopic)), payload, channel=self.channel)

    def new_subscription(self, inactivity_timeout=None):
        subscription = subscribe(str(SubTopic(self.pubtopic)), inactivity_timeout=inactivity_timeout)

        def subscription_with_errors():
            while True:
                message = next(subscription)
                if not message:
                    self.propagate_error(inactivity_timeout=SHORT_TIMEOUT)
                yield message

        return subscription_with_errors()

    def propagate_error(self, inactivity_timeout=None):
        body = next(consume(self.error_queue, inactivity_timeout=inactivity_timeout))
        if body:
            raise ComponentFailure(body["metadata"]["traceback"])


class amqp_component(AMQPComponent):
    def __enter__(self) -> AMQPComponent:
        super().__enter__()
        purge_queue(self.error_queue)
        if not _LIVE_COMPONENTS[self.func]:
            purge_queue(self.queue)
        _LIVE_COMPONENTS[self.func] += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _LIVE_COMPONENTS[self.func] -= 1
        super().__exit__(exc_type, exc_val, exc_tb)


def publish(routing_key, payload: Dict, channel=None):
    channel = channel or new_channel()
    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in retries(200, 0.1, pika.exceptions.UnroutableError):
        with retry():
            body = json.dumps(payload).encode()
            channel.basic_publish(exchange=EXCHANGE, routing_key=str(PubTopic(routing_key)), body=body, mandatory=True)


def subscribe(routing_key, inactivity_timeout=None):
    channel = new_channel()
    queue_name = channel.queue_declare(
        queue="",
        exclusive=True,
    ).method.queue
    channel.queue_bind(queue_name, EXCHANGE, routing_key=routing_key)

    return consume(queue_name, inactivity_timeout=inactivity_timeout, channel=channel)


def consume(queue_name, inactivity_timeout=None, channel=None) -> Iterator:
    channel = channel or new_channel()
    try:
        for _, _, body in channel.consume(queue_name, inactivity_timeout=inactivity_timeout):
            if body:
                yield json.loads(body)
            else:
                yield None
    finally:
        channel.close()


def purge_queue(queue_name: str):
    channel = new_channel()
    try:
        channel.queue_purge(queue_name)
    except pika.exceptions.ChannelClosedByBroker as exc:
        if "no queue" not in str(exc):
            raise


def new_channel() -> BlockingChannel:
    for retry in retries(40, 0.5, pika.exceptions.AMQPConnectionError):
        with retry():
            connection = pika.BlockingConnection(pika.URLParameters(AMQP_HOST))

    for retry in retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()

    return channel


class ComponentFailure(BaseException):
    pass
