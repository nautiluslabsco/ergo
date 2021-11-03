import pika
import pika.exceptions
import json
import uuid
import time
from typing import Type
from contextlib import contextmanager
from ergo_python.config import Graph


class ErgoRPCClient(object):
    """
    ErgoRPCClient provides a wrapper around ergo Graph objects for making synchronous remote procedure calls
    that publish to the given subtopic and then yield from the given pubtopic.

    >>> graph = Graph({"subtopic": "product_map", "pubtopic": "product_reduce"})
    >>> ergo_client = ErgoRPCClient(graph)
    >>> next(ergo_client.call(xs=[4, 5, 6]))
    120.0

    """

    def __init__(self, graph: Graph):
        self._graph = graph

        for retry in _retries(40, 0.5, pika.exceptions.AMQPConnectionError):
            with retry():
                self.connection = pika.BlockingConnection(pika.URLParameters(graph.host or ""))

        for retry in _retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
            with retry():
                self.channel = self.connection.channel()
                self.channel.exchange_declare(graph.exchange, passive=True)

        self.callback_queue = self.channel.queue_declare(
            queue="",
            exclusive=True,
        ).method.queue
        self.reply_to_topic = str(graph.pubtopic.extend(self.callback_queue))
        self.channel.queue_bind(self.callback_queue, graph.exchange, routing_key=self.reply_to_topic)

    def call(self, **payload):
        # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
        # of the dead letter queue.
        self.channel.confirm_delivery()
        for retry in _retries(10, 0.5, pika.exceptions.UnroutableError):
            with retry():
                body = json.dumps({"data": payload}).encode()
                correlation_id = str(uuid.uuid4())
                properties = pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=correlation_id,
                )
                self.channel.basic_publish(
                    exchange=self._graph.exchange,
                    routing_key=str(self._graph.subtopic),
                    body=body,
                    properties=properties,
                    mandatory=True,
                )

        for _, props, body in self.channel.consume(self.callback_queue):
            if props.correlation_id != correlation_id:
                continue
            message = json.loads(body)
            if "error" in message:
                raise RuntimeError(message["error"])
            yield message["data"]


def _retries(n: int, backoff_seconds: float, *retry_errors: Type[BaseException]):
    retry_errors = retry_errors or (Exception,)

    success: set = set()
    for attempt in range(n):
        if success:
            break

        @contextmanager
        def retry():
            try:
                yield
                success.add(True)
            except retry_errors:
                if attempt+1 == n:
                    raise
                time.sleep(backoff_seconds)

        yield retry
