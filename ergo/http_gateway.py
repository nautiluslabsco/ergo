import asyncio
from typing import AsyncGenerator, Dict, Tuple, Union, List

import aio_pika
import aiomisc
import hypercorn.asyncio
import hypercorn.config
from quart import Quart, request

from ergo.amqp_invoker import set_param
from ergo.config import Config
from ergo.message import Message, decode, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import defer_termination, instance_id, uniqueid

EVENT_LOOP_THREADS = 10
MAX_CONCURRENT_RPCS = 10**4
RPC_TIMEOUT = 60 * 60  # seconds
PORT = 80


class HttpGatewayServer:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._loop = aiomisc.new_event_loop(pool_size=EVENT_LOOP_THREADS)
        self._exchange, self._queue = self._loop.run_until_complete(self._setup_amqp(config))
        self._concurrent_rpcs_limiter = asyncio.Semaphore(MAX_CONCURRENT_RPCS)
        self._rpc_return_ready: Dict[str, asyncio.Condition] = {}
        self._rpc_return_values: Dict[str, Union[Message, List[Message]]] = {}

    def run(self) -> int:
        rpc_consumer_loop = self._loop.create_task(self._run_rpc_consumer())
        try:
            self._loop.run_until_complete(self._run_server())
        finally:
            rpc_consumer_loop.cancel()
        return 0

    async def _run_server(self):
        app = Quart(__name__)

        @app.route("/<path:path>", methods=["GET", "POST"])
        async def route(path: str):
            with defer_termination():
                async with self._concurrent_rpcs_limiter:
                    return await route_inner(path)

        async def route_inner(path: str):
            topic = path.replace("/", ".")
            results = await self._rpc(topic, request.args)
            return encodes(results)

        hypercorn_config = hypercorn.config.Config()
        hypercorn_config.bind = [f"0.0.0.0:{PORT}"]

        await hypercorn.asyncio.serve(app, hypercorn_config)

    async def _rpc(self, topic: str, data: dict) -> Union[Message, List[Message]]:
        message = decode(**data)
        message.key = topic
        message.scope.reply_to = instance_id()
        correlation_id = message.scope.correlation_id = uniqueid()

        self._rpc_return_ready[correlation_id] = asyncio.Condition()
        try:
            amqp_message = aio_pika.Message(body=encodes(message).encode("utf-8"))
            routing_key = str(PubTopic(message.key))
            await self._exchange.publish(amqp_message, routing_key)
            async with self._rpc_return_ready[correlation_id]:
                await self._rpc_return_ready[correlation_id].wait()
            return self._rpc_return_values.pop(correlation_id)
        finally:
            del self._rpc_return_ready[correlation_id]

    async def _run_rpc_consumer(self):
        async for amqp_message in self._queue:
            amqp_message.ack()
            ergo_message = decodes(amqp_message.body.decode("utf-8"))
            correlation_id = ergo_message.scope.correlation_id
            do_notify = True
            if ergo_message.stream:
                if correlation_id not in self._rpc_return_values:
                    self._rpc_return_values[correlation_id] = []
                if ergo_message.stream == 1:
                    self._rpc_return_values[correlation_id].append(ergo_message)
                    do_notify = False
            else:
                self._rpc_return_values[correlation_id] = ergo_message
            if do_notify:
                async with self._rpc_return_ready[correlation_id]:
                    self._rpc_return_ready[correlation_id].notify()

    async def _setup_amqp(self, config: Config) -> Tuple[aio_pika.Exchange, aio_pika.Queue]:
        host = self._config.host
        heartbeat = self._config.heartbeat
        broker_url = set_param(host, "heartbeat", str(heartbeat)) if heartbeat else host
        connection: aio_pika.Connection = await aio_pika.connect_robust(broker_url)
        channel: aio_pika.Channel = await connection.channel()
        exchange: aio_pika.Exchange = await channel.declare_exchange(name=config.exchange, passive=True)
        queue: aio_pika.Queue = await channel.declare_queue(name=f"gateway/{instance_id()}", exclusive=True)
        await queue.bind(exchange=exchange, routing_key=str(SubTopic(instance_id())))
        return exchange, queue
