"""Summary."""
import asyncio
import json
from typing import Dict, Iterable
from urllib.parse import urlparse

import aio_pika
import aiomisc
from retry import retry

from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.payload import Payload
from ergo.types import TYPE_PAYLOAD
from ergo.util import extract_from_stack

# content_type: application/json
# {"x":5,"y":7}

MAX_THREADS = 2


def set_param(host: str, param_key: str, param_val: str) -> str:
    """Overwrite a param in a host string w a new value."""
    uri, new_param = urlparse(host), f'{param_key}={param_val}'
    params = [p for p in uri.query.split('&') if param_key not in p] + [new_param]
    return uri._replace(query='&'.join(params)).geturl()


def make_error_output(err: Exception) -> Dict[str, str]:
    """Make a more digestable error output."""
    orig = err.__context__ or err
    err_output = {
        'type': type(orig).__name__,
        'message': str(orig),
    }
    filename, lineno, function_name = extract_from_stack(orig)
    if None not in (filename, lineno, function_name):
        err_output = {**err_output, 'file': filename, 'line': lineno, 'func': function_name}
    return err_output


class AmqpInvoker(Invoker):
    """Summary."""

    def __init__(self, invocable: FunctionInvocable) -> None:
        super().__init__(invocable)

        host = self._invocable.config.host
        heartbeat = self._invocable.config.heartbeat

        self.url = set_param(host, 'heartbeat', str(heartbeat)) if heartbeat else host
        self.exchange_name = self._invocable.config.exchange
        self.queue_name = self._invocable.config.func

    def start(self) -> int:
        """
        Starts a new event loop that maintains a persistent AMQP connection. The underlying execution context is an `aiomisc.ThreadPoolExecutor` of size `MAX_THREADS`.

        Returns:
            exit_code
        """
        loop = aiomisc.new_event_loop(pool_size=MAX_THREADS)
        connection = loop.run_until_complete(self.run(loop))

        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(connection.close())

        return 0

    @retry((aio_pika.exceptions.AMQPError, aio_pika.exceptions.ChannelInvalidStateError), delay=0.5, jitter=(1, 3), backoff=2)
    async def run(self, loop: asyncio.AbstractEventLoop) -> aio_pika.RobustConnection:
        """Establishes the AMQP connection with rudimentary retry logic on `aio_pika.exceptions.AMQPError` and `aio_pika.exceptions.ChannelInvalidStateError`.
        Runs continuous `consume` -> `do_work` -> `publish` event loop.

        Parameters:
            loop: Asyncio-compliant event loop primitive that is responsible for scheduling work
        Returns:
            connection: Connection that attempts to restore state (channels, queues, etc.) upon reconnects
        """
        connection = await aio_pika.connect_robust(url=self.url, loop=loop)

        async def get_channel() -> aio_pika.Channel:
            return await connection.channel()

        # Pool for consuming and publishing
        channel_pool = aio_pika.pool.Pool[aio_pika.RobustChannel](get_channel, max_size=2, loop=loop)
        async with channel_pool.acquire() as channel:
            await channel.declare_exchange(name=self.exchange_name, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True, auto_delete=False, internal=False, arguments=None)

        # Consume-Publish loop
        async with connection, channel_pool:
            async for data_in in self.consume(channel_pool):
                try:
                    data_in.set('context', self._invocable.config.copy())

                    async for data_out in self.do_work(data_in):
                        message = aio_pika.Message(body=json.dumps(data_out).encode())
                        routing_key = str(data_in.get('context').pubtopic)
                        await self.publish(channel_pool, message, routing_key=routing_key)

                except Exception as err:  # pylint: disable=broad-except
                    data_in.set('error', make_error_output(err))
                    data_in.set('traceback', str(err))
                    data_in.unset('context')
                    message = aio_pika.Message(body=str(data_in).encode())
                    routing_key = f'{self.queue_name}_error'
                    await self.publish(channel_pool, message, routing_key)

        return connection

    async def consume(self, channel_pool: aio_pika.pool.Pool[aio_pika.RobustChannel]) -> Iterable[TYPE_PAYLOAD]:
        """
        Re-acquires handles to `channel`, `exchange`, and `queue` before continuously consuming `aio_pika.IncomingMessage`.

        Parameters:
            channel_pool: Pool of valid `Channel` handles

        Yields:
            payload: JSON-deserialized object
        """

        async with channel_pool.acquire() as channel:
            # See: https://github.com/mosquito/aio-pika/issues/396
            # Exchange should be guaranteed to exist at this point, unless manually deleted from outside the system (in which case this ought to fail)
            # This simply refreshes the handle
            exchange = await channel.get_exchange(name=self.exchange_name, ensure=False)
            queue = await channel.declare_queue(name=self.queue_name)
            queue_error = await channel.declare_queue(name=f'{self.queue_name}_error')

            await queue.bind(exchange=exchange, routing_key=str(self._invocable.config.subtopic))
            await queue_error.bind(exchange=exchange, routing_key=f'{self.queue_name}_error')

            async for message in queue:
                async with message.process():
                    data_in = json.loads(message.body.decode('utf-8'))
                    yield Payload(data_in)

    async def publish(self, channel_pool: aio_pika.pool.Pool[aio_pika.RobustChannel], message: aio_pika.Message, routing_key: str) -> None:
        """
        Re-acquires handles to `channel`, `exchange`, and `queue` before publishing message.

        Parameters:
            channel_pool: Pool of valid `Channel` handles
            message: Message to be published
            routing_key: Exchange-level routing discriminator
        """
        async with channel_pool.acquire() as channel:
            exchange = await channel.get_exchange(name=self.exchange_name, ensure=False)
            await exchange.publish(message, routing_key)

    @aiomisc.threaded_iterable_separate
    def do_work(self, data_in: TYPE_PAYLOAD) -> Iterable[TYPE_PAYLOAD]:
        """
        Performs the potentially long-running work of `self._invocable.invoke` in a separate thread
        within the constraints of the underlying execution context.

        Parameters:
            data_in: Raw event data

        Yields:
            payload: Lazily-evaluable wrapper around return values from `self._invocable.invoke`, plus metadata
        """

        for data_out in self._invocable.invoke(data_in):
            yield {'data': data_out, 'key': str(data_in.get('context').pubtopic), 'log': data_in.get('log', [])}
