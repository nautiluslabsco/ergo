from pathlib import Path
import inspect

import json
import pika
import pika.exceptions
from ergo.topic import PubTopic
from test.integration.utils import retries
from contextlib import contextmanager
from pika.adapters.blocking_connection import BlockingChannel
from test.integration.utils import retries
from typing import ContextManager, Iterator, Iterable, Callable, Optional


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "test_exchange"


class Component:
    def __init__(self, func: Callable, subtopic: str, pubtopic: Optional[str]):
        self.func = func
        self.subtopic = subtopic
        self.pubtopic = pubtopic
        self.channel = new_channel()
        self.error_queue = f"{inspect.getfile(func)}:{func.__name__}_error"
        self.channel.queue_purge(self.error_queue)

    @property
    def manifest(self):
        return {
            "func": f"{inspect.getfile(self.func)}:{self.func.__name__}"
        }

    @property
    def namespace(self):
        namespace = {
            "protocol": "amqp",
            "host": AMQP_HOST,
            "exchange": "test_exchange",
            "subtopic": self.subtopic
        }
        if self.pubtopic:
            namespace["pubtopic"] = self.pubtopic
        return namespace

    def propagate_error(self, inactivity_timeout=None):
        method, _, body = next(consume(self.error_queue, inactivity_timeout))
        if body:
            self.channel.basic_ack(method.delivery_tag)
            error = json.loads(body)["error"]
            raise ComponentFailure(error)


def publish(routing_key, payload: str):
    channel = new_channel()
    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in retries(20, 0.5, pika.exceptions.UnroutableError):
        with retry():
            channel.basic_publish(exchange=EXCHANGE, routing_key=str(PubTopic(routing_key)), body=payload.encode(), mandatory=True)


class ErrorConsumer:
    def __init__(self, functions: Iterable[Callable]):
        self.channel = new_channel()
        for function in functions:
            file = inspect.getfile(function)
            queue_name = f"{file}:{function.__name__}_error"


def poll_errors(functions: Iterable[Callable], inactivity_timeout=None):
    for function in functions:
        file = inspect.getfile(function)
        queue_name = f"{file}:{function.__name__}_error"
        _, _, body = next(consume(queue_name, inactivity_timeout))
        if not body:
            continue
        error = json.loads(body)["error"]
        raise ComponentFailure(error)


def subscribe(routing_key, inactivity_timeout=None):
    channel = new_channel()
    queue_name = channel.queue_declare(
        queue="",
        exclusive=True,
    ).method.queue
    channel.queue_bind(queue_name, EXCHANGE, routing_key=routing_key)

    return channel.consume(queue_name, inactivity_timeout=inactivity_timeout)


def consume(queue_name, inactivity_timeout=None):
    channel = new_channel()
    try:
        yield from channel.consume(queue_name, inactivity_timeout=inactivity_timeout)
    finally:
        channel.close()


def new_channel() -> BlockingChannel:
    for retry in retries(40, 0.5, pika.exceptions.AMQPConnectionError):
        with retry():
            connection = pika.BlockingConnection(pika.URLParameters(AMQP_HOST))

    for retry in retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()
            channel.exchange_declare(EXCHANGE, passive=True)

    return channel


class ComponentFailure(BaseException):
    pass
