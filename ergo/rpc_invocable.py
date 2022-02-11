from typing import AsyncGenerator, cast

import aio_pika
from quart import Quart, request

from ergo.amqp_invoker import set_param
from ergo.http_invoker import HttpInvoker
from ergo.message import Message, decode, decodes, encodes
from ergo.topic import PubTopic
from ergo.util import instance_id, uniqueid

MAX_THREADS = 2
AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


class QuartHttpGateway(HttpInvoker):
    def __init__(self, config) -> None:
        super().__init__(None)
        self._config = config
        self._connection = None
        self._channel = None
        self._exchange = None
        self._queue = None
        host = self._config.host
        heartbeat = self._config.heartbeat
        self._url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host

    def start(self) -> int:
        app = Quart(__name__)

        @app.route('/<path:path>', methods=['GET', 'POST'])
        async def handler(path: str):
            topic = path.replace('/', '.')
            message_in: Message = decode(**request.args)
            message_in.key = topic
            # TODO do we do if multiple results are being yielded by a generator?
            message_out = await self._invoke(message_in).__anext__()
            return encodes(message_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0

    async def _invoke(self, message: Message) -> AsyncGenerator[Message, None]:
        correlation_id = uniqueid()
        message.scope.reply_to = f"{instance_id()}.{correlation_id}"
        amqp_message = aio_pika.Message(body=encodes(message).encode('utf-8'))
        routing_key = str(PubTopic(message.key))
        exchange = await self.exchange()
        await exchange.publish(amqp_message, routing_key)
        result = await self._consume(correlation_id)
        yield result

    async def _consume(self, correlation_id: str) -> Message:
        queue = await self.queue()
        async for amqp_message in queue:
            # TODO use amqp's reply_to and correlation id so that we don't have to deserialize all of these?
            amqp_message = cast(aio_pika.IncomingMessage, amqp_message)
            ergo_message = decodes(amqp_message.body.decode('utf-8'))
            assert ergo_message.scope.reply_to
            _, corrid = ergo_message.scope.reply_to.split(".")
            if correlation_id == corrid:
                return ergo_message

    async def connection(self) -> aio_pika.RobustConnection:
        if not self._connection:
            self._connection = await aio_pika.connect_robust(url=self._url)
        return self._connection

    async def channel(self) -> aio_pika.Channel:
        if not self._channel:
            connection = await self.connection()
            self._channel = await connection.channel()
        return self._channel

    async def exchange(self) -> aio_pika.Exchange:
        if not self._exchange:
            channel = await self.channel()
            self._exchange = await channel.declare_exchange(name=self._config.exchange, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True, auto_delete=False, internal=False, arguments=None)
        return self._exchange

    async def queue(self) -> aio_pika.Queue:
        if not self._queue:
            channel = await self.channel()
            self._queue = await channel.declare_queue(name=f"rpc/{instance_id()}", exclusive=True)
        return self._queue

