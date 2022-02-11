from ergo.invocable import Invocable
from ergo.message import Message
from ergo.util import instance_id, uniqueid
from ergo.amqp_invoker import set_param
from typing import AsyncGenerator
import aio_pika
import inspect
import inspect
from typing import List, cast
from flask import Flask, request
from ergo.http_invoker import HttpInvoker
from ergo.message import Message, decodes, decode, encodes
from ergo.topic import PubTopic
import asyncio
from ergo.config import Config
from functools import lru_cache
import aiomisc


MAX_THREADS = 2
AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


class FlaskHttpGateway(HttpInvoker):
    def __init__(self, config) -> None:
        """Summary.

        Args:
            invocable (Invocable): Description

        """
        super().__init__(None)
        self._config = config

    def start(self) -> int:
        loop = aiomisc.new_event_loop(pool_size=MAX_THREADS)
        return loop.run_until_complete(self.run(loop))

    async def run(self, loop: asyncio.AbstractEventLoop):
        host = self._config.host
        heartbeat = self._config.heartbeat
        url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host
        connection: aio_pika.RobustConnection = await aio_pika.connect_robust(url=url, loop=loop)
        self._channel: aio_pika.RobustChannel = await connection.channel()
        self._exchange = await self._channel.declare_exchange(name=self._config.exchange, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True, auto_delete=False, internal=False, arguments=None)
        self._queue = await self._channel.declare_queue(name=f"rpc/{instance_id()}", exclusive=True)

        app: Flask = Flask(__name__)

        @app.route('/<path:path>', methods=['GET', 'POST'])
        async def handler(path: str):
            topic = path.replace('/', '.')
            message_in: Message = decode(**request.args)
            message_in.key = topic
            # TODO do we do if multiple results are being yielded by a generator?
            message_out = await self.invoke_handler(message_in).__anext__()
            return encodes(message_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0


class RPCInvocable(Invocable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        host = self.config.host
        heartbeat = self.config.heartbeat
        self._url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host
        self._queue = None

    # async def init(self):
    #     connection: aio_pika.RobustConnection = await aio_pika.connect_robust(url=self._url)
    #     self._channel: aio_pika.RobustChannel = await connection.channel()
    #     self._exchange = await self._channel.declare_exchange(name=self.config.exchange, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True, auto_delete=False, internal=False, arguments=None)
    #     self._queue = await self._channel.declare_queue(name=f"rpc/{instance_id()}", exclusive=True)

    async def _connection(self) -> aio_pika.RobustConnection:
        return await aio_pika.connect_robust(url=self._url)

    async def _channel(self) -> aio_pika.Channel:
        connection = await self._connection()
        channel = await connection.channel()
        # await channel.initialize()
        return channel

    async def _exchange(self) -> aio_pika.Exchange:
        channel = await self._channel()
        return await channel.declare_exchange(name=self.config.exchange, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True, auto_delete=False, internal=False, arguments=None)

    async def queue(self) -> aio_pika.Queue:
        if not self._queue:
            channel = await self._channel()
            self._queue = await channel.declare_queue(name=f"rpc/{instance_id()}", exclusive=True)
        return self._queue

    async def invoke(self, message: Message) -> AsyncGenerator[Message, None]:
        correlation_id = uniqueid()
        message.scope.reply_to = f"{instance_id()}.{correlation_id}"
        amqp_message = aio_pika.Message(body=encodes(message).encode('utf-8'))
        routing_key = str(PubTopic(message.key))
        exchange = await self._exchange()
        await exchange.publish(amqp_message, routing_key)
        result = await self.consume(correlation_id)
        yield result

    async def consume(self, correlation_id: str) -> Message:
        queue = await self.queue()
        async for amqp_message in queue:
            # TODO use amqp's reply_to and correlation id so that we don't have to deserialize all of these?
            amqp_message = cast(aio_pika.IncomingMessage, amqp_message)
            ergo_message = decodes(amqp_message.body.decode('utf-8'))
            assert ergo_message.scope.reply_to
            _, corrid = ergo_message.scope.reply_to.split(".")
            if correlation_id == corrid:
                return ergo_message
