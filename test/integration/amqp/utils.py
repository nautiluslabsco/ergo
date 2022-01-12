import inspect
import json
import pika
import pika.exceptions
from ergo.topic import SubTopic
from pika.adapters.blocking_connection import BlockingChannel
from test.integration.utils import Component, retries
from typing import Iterator, Callable, Optional
from ergo.topic import PubTopic
from contextlib import contextmanager
from collections import defaultdict

AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "test_exchange"
_LIVE_COMPONENTS = defaultdict(int)


class AMQPComponent(Component):
    protocol = "amqp"
    host = AMQP_HOST

    def __init__(self, func: Callable, subtopic: str, pubtopic: Optional[str]):
        super().__init__(func)
        self.subtopic = subtopic
        self.pubtopic = pubtopic
        self.channel = new_channel()

    @property
    def namespace(self):
        ns = super().namespace
        ns["subtopic"] = self.subtopic
        if self.pubtopic:
            ns["pubtopic"] = self.pubtopic
        return ns

    def rpc(self, **payload):
        subscription = self.subscribe()
        self.publish(channel=self.channel, **payload)
        yield from subscription

    def publish(self, **payload):
        publish(str(PubTopic(self.subtopic)), **payload)

    def subscribe(self, inactivity_timeout=None):
        return subscribe(str(SubTopic(self.pubtopic)), inactivity_timeout=inactivity_timeout)

    def propagate_error(self, inactivity_timeout=None):
        body = next(consume(self.error_queue, inactivity_timeout=inactivity_timeout))
        if body:
            raise ComponentFailure(body["metadata"]["traceback"])


@contextmanager
def amqp_component(func: Callable, subtopic: str, pubtopic: Optional[str]) -> AMQPComponent:
    component = AMQPComponent(func, subtopic=subtopic, pubtopic=pubtopic)
    with component.start():
        for retry in retries(200, 0.01, pika.exceptions.ChannelClosedByBroker):
            with retry():
                purge_queue(component.error_queue)
                break
        key = component.func
        if not _LIVE_COMPONENTS[key]:
            purge_queue(component.queue)
        _LIVE_COMPONENTS[key] += 1
        try:
            yield component
        finally:
            _LIVE_COMPONENTS[key] -= 1


def publish(routing_key, channel=None, **payload):
    channel = channel or new_channel()
    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in retries(20, 0.5, pika.exceptions.UnroutableError):
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
