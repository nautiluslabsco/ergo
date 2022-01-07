import pika
import pika.exceptions
import json
import uuid
import time
from typing import Type
from contextlib import contextmanager
from ergo.config import Config
from ergo.types import TYPE_PAYLOAD
from ergo.topic import SubTopic, PubTopic


class RPCInvocable:
    def __init__(self, config: Config):
        self._config = config

        for retry in _retries(40, 0.5, pika.exceptions.AMQPConnectionError):
            with retry():
                self.connection = pika.BlockingConnection(pika.URLParameters(config.host or ""))

        for retry in _retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
            with retry():
                self.channel = self.connection.channel()
                self.channel.exchange_declare(config.exchange, passive=True)

        self.callback_queue = self.channel.queue_declare(
            queue="",
            exclusive=True,
        ).method.queue
        self.reply_to_topic = str(SubTopic(f"{config.rpc_target}.{self.callback_queue}.rpc_out"))
        self.channel.queue_bind(self.callback_queue, config.exchange, routing_key=self.reply_to_topic)

    def invoke(self, data_in: TYPE_PAYLOAD):
        # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
        # of the dead letter queue.
        self.channel.confirm_delivery()
        for retry in _retries(10, 0.5, pika.exceptions.UnroutableError):
            with retry():
                body = json.dumps(data_in).encode()
                correlation_id = str(uuid.uuid4())
                properties = pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=correlation_id,
                )
                self.channel.basic_publish(
                    exchange=self._config.exchange,
                    routing_key=str(PubTopic(f"{self._config.rpc_target}.rpc_in")),
                    body=body,
                    properties=properties,
                    mandatory=True,
                )

        for _, props, body in self.channel.consume(self.callback_queue):
            if props.correlation_id != correlation_id:
                continue
            yield body


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
