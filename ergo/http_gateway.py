import asyncio
import functools
import yaml
from typing import AsyncGenerator, Dict, Tuple, cast
import threading

import os
import aio_pika
import aiomisc
from quart import Quart, request

from ergo.amqp_invoker import set_param
from ergo.config import Config
from ergo.message import Message, decode, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import instance_id, uniqueid

MAX_THREADS = 8

app = Quart(__name__)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "up"}


@app.route("/<path:path>", methods=["GET", "POST"])
async def handler(path: str):
    topic = path.replace("/", ".")
    # TODO what do we do if multiple results are being yielded by a generator?
    #  We're not injecting the handler, so we can't inspect for that.
    message_out = await rpc(topic, request.args).__anext__()
    return encodes(message_out)


async def rpc(topic: str, data: dict) -> AsyncGenerator[Message, None]:
    client = get_rpc_client()
    async for message in client.rpc(topic, data):
        yield message


@functools.lru_cache
def get_rpc_client():
    return RPCClient()


class RPCClient:
    def __init__(self):
        config = load_config()
        self._port = 80
        # self._loop = aiomisc.new_event_loop(pool_size=MAX_THREADS)
        self._lock = asyncio.Lock()
        self._loop = asyncio.get_running_loop()
        self._setup_event = asyncio.Event()
        # self._exchange, self._queue = self._loop.run_until_complete(self._setup(config))
        self._publishers: Dict[str, asyncio.Condition] = {}
        self._inbox: Dict[str, Message] = {}
        self._setup_task = self._loop.create_task(self._setup(config))
        self._consumer_task = self._loop.create_task(self._run_consumer())
        # self._consumer_task = self._loop.call_soon(self._run_consumer)

    async def rpc(self, topic: str, data: dict) -> AsyncGenerator[Message, None]:
        message = decode(**data)
        message.key = topic

        correlation_id = uniqueid()
        self._publishers[correlation_id] = asyncio.Condition()
        try:
            message.scope.reply_to = f"{instance_id()}.{correlation_id}"
            amqp_message = aio_pika.Message(
                body=encodes(message).encode("utf-8"), correlation_id=correlation_id
            )
            routing_key = str(PubTopic(message.key))
            exchange = await self.exchange()
            await exchange.publish(amqp_message, routing_key)
            bh = True
            async with self._publishers[correlation_id]:
                await self._publishers[correlation_id].wait()
            yield self._inbox.pop(correlation_id)
        finally:
            del self._publishers[correlation_id]

    async def _run_consumer(self):
        print("here")
        queue = await self.queue()
        messages = queue.iterator()
        # async for amqp_message in queue:
        while True:
            amqp_message = await messages.__anext__()
            amqp_message = cast(amqp_message, aio_pika.IncomingMessage)
            print(amqp_message)
            try:
                amqp_message.ack()
                ergo_message = decodes(amqp_message.body.decode("utf-8"))
                self._inbox[amqp_message.correlation_id] = ergo_message
            finally:
                print("a")
                async with self._publishers[amqp_message.correlation_id]:
                    self._publishers[amqp_message.correlation_id].notify()
                print("b")

    async def queue(self) -> aio_pika.Queue:
        await self._setup_event.wait()
        return self._queue

    async def exchange(self) -> aio_pika.Exchange:
        await self._setup_event.wait()
        return self._exchange

    async def _setup(self, config: Config):
        host = config.host
        heartbeat = config.heartbeat
        broker_url = set_param(host, "heartbeat", str(heartbeat)) if heartbeat else host

        connection: aio_pika.Connection = await aio_pika.connect_robust(broker_url)
        channel: aio_pika.Channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        self._exchange: aio_pika.Exchange = await channel.declare_exchange(
            name=config.exchange,
            type=aio_pika.ExchangeType.TOPIC,
            passive=False,
            durable=True,
            auto_delete=False,
            internal=False,
            arguments=None,
        )
        self._queue: aio_pika.Queue = await channel.declare_queue(
            name=f"rpc/{instance_id()}", exclusive=True
        )
        await self._queue.bind(exchange=self._exchange, routing_key=str(SubTopic(instance_id())))
        self._setup_event.set()


def load_config() -> Config:
    path = os.getenv("ERGO_CONFIG", "ergo.yml")
    with open(path) as fh:
        config = Config(yaml.safe_load(fh))
    return config


class QuartHttpGateway:
    pass
