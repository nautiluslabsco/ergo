"""Summary."""
import json
from typing import Callable, Tuple
from urllib.parse import urlparse
from black import asyncio
from markupsafe import functools
import pika
from src.function_invocable import FunctionInvocable
from src.invoker import Invoker
from src.types import TYPE_PAYLOAD
import aio_pika

# content_type: application/json
# {"x":5,"y":7}


def set_param(host: str, param_key: str, param_val: str) -> str:
    """Overwrite a param in a host string w a new value."""
    uri, new_param = urlparse(host), f'{param_key}={param_val}'
    params = [p for p in uri.query.split('&') if param_key not in p] + [new_param]
    return uri._replace(query='&'.join(params)).geturl()


class AmqpInvoker(Invoker):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        super().__init__(invocable)

        host = self._invocable.config.host
        heartbeat = self._invocable.config.heartbeat

        self.url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host
        self.exchange_name = self._invocable.config.exchange
        self.queue_name = self._invocable.config.func

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        connection = loop.run_until_complete(self.connect(loop))

        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(connection.close())

    async def connect(self, loop: asyncio.AbstractEventLoop) -> aio_pika.RobustConnection:
        connection = await aio_pika.connect_robust(url=self.url, loop=loop)

        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                name=self.exchange_name,
                type=aio_pika.ExchangeType.TOPIC,
                passive=False,
                durable=True,
                auto_delete=False,
                internal=False,
                arguments=None
            )
            queue = await channel.declare_queue(name=self.queue_name)
            queue_error = await channel.declare_queue(name=f'{self.queue_name}_error')

            await queue.bind(exchange=exchange, routing_key=str(self._invocable.config.subtopic))
            # TODO(ahuman-bean): bind error queue

            async def handler():
                await queue.consume(functools.partial(self.on_message, channel=channel))

            async def error_handler():
                await queue_error.consume(functools.partial(self.on_error, channel=channel))

            await loop.create_task(handler())
            await loop.create_task(error_handler())

        return connection

    async def on_message(self, message: aio_pika.IncomingMessage, channel: aio_pika.RobustChannel):
        async with message.process():
            data_in: TYPE_PAYLOAD = dict(json.loads(message.body.decode('utf-8')))
            exchange = await channel.get_exchange(self._invocable.config.exchange)

            try:
                for data_out in self._invocable.invoke(data_in["data"]):
                    payload = {
                        "data": data_out,
                        "key": str(self._invocable.config.pubtopic),
                        "log": data_in.get("log", []),
                    }
                    await exchange.publish(message=aio_pika.Message(body=json.dumps(payload).encode()), routing_key=str(self._invocable.config.pubtopic))

            except Exception as err:  # pylint: disable=broad-except
                data_in['error'] = str(err)
                # TODO(ahuman-bean): cleaner error messages
                await exchange.publish(message=aio_pika.Message(body=json.dumps(data_in).encode()), routing_key=f'{self.queue_name}_error')

    async def on_error(message: aio_pika.IncomingMessage, channel: aio_pika.RobustChannel):
        pass
