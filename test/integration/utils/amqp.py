from __future__ import annotations

import amqp.exceptions
import contextlib
import inspect
import json
import pathlib
import socket
from functools import wraps
from test.integration.utils import FunctionComponent, retries
from typing import Callable, Dict, List, Optional, Iterable, cast
import kombu
import kombu.simple
import kombu.pools
from amqp import Channel

import pika
import pika.exceptions
import pytest
from pika.adapters.blocking_connection import BlockingChannel

from ergo.topic import SubTopic

try:
    from collections.abc import Generator
except ImportError:
    from typing import Generator

from collections import defaultdict

from ergo.topic import PubTopic
from ergo.message import Message, decodes

AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
CONNECTION = kombu.Connection(AMQP_HOST)
EXCHANGE = "amq.topic"  # use a pre-declared exchange that we kind bind to while the ergo runtime is booting
# EXCHANGE = "my_exchange"
SHORT_TIMEOUT = 0.01
LONG_TIMEOUT = 5
_LIVE_INSTANCES: Dict = defaultdict(int)


class AMQPComponent(FunctionComponent):
    protocol = "amqp"
    instances: List[AMQPComponent] = []

    def __init__(
        self,
        func: Callable,
        subtopic: Optional[str] = None,
        pubtopic: Optional[str] = None,
        **manifest
    ):
        super().__init__(func, **manifest)
        self.queue_name = f"{self.handler_path.replace('/', ':')[1:]}:{self.handler_name}"
        self.error_queue_name = f"{self.queue_name}:error"
        handler_module = pathlib.Path(self.handler_path).with_suffix("").name
        self.subtopic = subtopic or f"{handler_module}_{self.handler_name}_sub"
        self.pubtopic = pubtopic or f"{handler_module}_{self.handler_name}_pub"


    @property
    def namespace(self):
        ns = {
            "protocol": "amqp",
            "host": AMQP_HOST,
            "exchange": EXCHANGE,
            "subtopic": self.subtopic,
        }
        if self.pubtopic:
            ns["pubtopic"] = self.pubtopic
        return ns

    def rpc(self, inactivity_timeout=LONG_TIMEOUT, **payload):
        self.send(**payload)
        return self.consume(inactivity_timeout=inactivity_timeout)

    def send(self, **payload):
        publish(payload, self.subtopic)
        # self._component_queue.put(payload)

    def consume(self, inactivity_timeout=LONG_TIMEOUT):
        from dataclasses import asdict
        return asdict(self._subscription.get(timeout=inactivity_timeout))

    def __call__(self, test):
        params = inspect.signature(test).parameters

        if "component" in params:

            @wraps(test)
            @pytest.mark.parametrize("component", [self])
            def test_with_component(*args, component=None, **kwargs):
                with self:
                    return test(*args, component=component, **kwargs)

            return test_with_component
        if "components" in params:

            @wraps(test)
            @pytest.mark.parametrize("components", [AMQPComponent.instances])
            def test_with_component(*args, components=None, **kwargs):
                with self:
                    return test(*args, components=components, **kwargs)

            return test_with_component
        return test

    def __enter__(self):
        super().__enter__()

        with CONNECTION.channel() as channel:
            channel = cast(Channel, channel)
            try:
                channel.queue_purge(self.queue_name)
            except amqp.exceptions.NotFound:
                pass

        self.instances.append(self)
        # if not sum(_LIVE_INSTANCES.values()):
        #     with CONNECTION.channel() as channel:
        #         exchange = kombu.Exchange(EXCHANGE, type="topic", channel=channel)
        #         exchange.delete()

        # self._component_queue = ComponentQueue(self.queue_name)
        # self._component_queue.__enter__()
        if not _LIVE_INSTANCES[self.func]:
            self._subscription = Queue(self.pubtopic, name=f"test_subscription:{self.pubtopic}")
            self._subscription.__enter__()
        _LIVE_INSTANCES[self.func] += 1

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

        self.instances.pop()
        _LIVE_INSTANCES[self.func] -= 1
        if not _LIVE_INSTANCES[self.func]:
            # self._component_queue.__exit__()
            self._subscription.__exit__()


amqp_component = AMQPComponent


def publish(payload: dict, routing_key: str):
    with CONNECTION.channel() as channel:
        with kombu.Producer(channel, serializer="raw") as producer:
            producer.publish(json.dumps(payload), exchange=EXCHANGE, routing_key=str(PubTopic(routing_key)))


class ComponentFailure(Exception):
    pass


class Queue:
    def __init__(self, routing_key, name: Optional[str] = None, **kombu_opts):
        self.name = name or routing_key
        self.routing_key = routing_key
        self._kombu_opts = {"auto_delete": True, "durable": False, **kombu_opts}

        self._channel: Channel = CONNECTION.channel()
        exchange = kombu.Exchange(EXCHANGE, type="topic", channel=self._channel)
        self._spec = kombu.Queue(self.name, exchange=exchange, routing_key=str(PubTopic(self.routing_key)), no_ack=True, **self._kombu_opts)
        self._queue = kombu.simple.SimpleQueue(self._channel, self._spec, serializer="raw")
        if kombu_opts.get("durable"):
            while True:
                _, _, consumers = self._channel.queue_declare(self.name, passive=True)
                if consumers:
                    break

    def put(self, data: dict):
        self._queue.put(json.dumps(data), declare=[self._spec])

    def get(self, block=True, timeout=None) -> Message:
        amqp_message = self._queue.get(block=block, timeout=timeout)
        return decodes(amqp_message.body)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self._channel.queue_delete(self.name)
        self._channel.__exit__()


class ComponentQueue(Queue):
    def __init__(self, routing_key):
        super().__init__(routing_key, auto_delete=False, durable=True)


class propagate_errors:
    def __init__(self):
        self._queue = kombu.Queue("test_error_queue", exchange=EXCHANGE, routing_key="#", auto_delete=True, no_ack=True)

    def __enter__(self):
        self._channel: Channel = CONNECTION.channel()
        self._consumer = kombu.Consumer(self._channel, queues=[self._queue], callbacks=[self._handle_message])
        self._consumer.consume()
        return self

    def __exit__(self, *exc_info):
        self._consumer.close()
        self._channel.close()

    @staticmethod
    def _handle_message(body: str, _):
        ergo_msg = decodes(body)
        if ergo_msg.error:
            raise ComponentFailure(ergo_msg.traceback)


