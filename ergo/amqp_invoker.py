"""Summary."""
import asyncio
from typing import AsyncIterable, Dict, cast
from urllib.parse import urlparse

import aio_pika
import aiomisc
import jsons
from retry import retry

from ergo.function_invocable import FunctionInvocable
from ergo.invoker import Invoker
from ergo.message import Message, decodes, encodes
from ergo.topic import PubTopic, SubTopic
from ergo.util import extract_from_stack

# content_type: application/json
# {"x":5,"y":7}

MAX_THREADS = 2
CHANNEL_POOL_SIZE = 2  # minimum is 1 per active run_queue_loop coroutine


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
        self.component_queue_name = f"{self._invocable.config.func}"
        self.error_queue_name = f"{self.component_queue_name}_error"

    def start(self) -> int:
        """
        Starts a new event loop that maintains a persistent AMQP connection.
        The underlying execution context is an `aiomisc.ThreadPoolExecutor` of size `MAX_THREADS`.

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

    @retry((aio_pika.exceptions.AMQPError, aio_pika.exceptions.ChannelInvalidStateError),
           delay=0.5, jitter=(1, 3), backoff=2)
    async def run(self, loop: asyncio.AbstractEventLoop) -> aio_pika.RobustConnection:
        """
        Establishes the AMQP connection with rudimentary retry logic on `aio_pika.exceptions.AMQPError`
        and `aio_pika.exceptions.ChannelInvalidStateError`. Runs a continuous `consume` -> `do_work` -> `publish`
        event loop.

        Parameters:
            loop: Asyncio-compliant event loop primitive that is responsible for scheduling work
        Returns:
            connection: Connection that attempts to restore state (channels, queues, etc.) upon reconnects
        """
        connection: aio_pika.RobustConnection = await aio_pika.connect_robust(url=self.url, loop=loop)

        async def get_channel() -> aio_pika.Channel:
            return await connection.channel()

        # Pool for consuming and publishing
        channel_pool: aio_pika.pool.Pool[aio_pika.RobustChannel] = \
            aio_pika.pool.Pool(get_channel, max_size=CHANNEL_POOL_SIZE, loop=loop)
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                name=self.exchange_name, type=aio_pika.ExchangeType.TOPIC, passive=False, durable=True,
                auto_delete=False, internal=False, arguments=None)
            error_queue = await channel.declare_queue(name=self.error_queue_name)
            await error_queue.bind(exchange=exchange, routing_key=self.error_queue_name)
            component_queue = await channel.declare_queue(name=self.component_queue_name)
            await component_queue.bind(exchange=exchange, routing_key=str(SubTopic(self._invocable.config.subtopic)))

        async with connection, channel_pool:
            await self.run_queue_loop(channel_pool, component_queue)

        return connection

    async def run_queue_loop(self, channel_pool: aio_pika.pool.Pool, queue: aio_pika.Queue):
        async for message in self.consume(queue):
            await self.handle_message(message, channel_pool)

    @staticmethod
    async def consume(queue: aio_pika.Queue) -> AsyncIterable[Message]:
        """
        Continuously consume AMQP messages from the given queue, yielding ergo Messages parsed from their contents.

        Parameters:
            queue: aio_pika.Queue

        Yields:
            message: ergo.message.Message
        """
        async for amqp_message in queue:
            amqp_message = cast(aio_pika.IncomingMessage, amqp_message)
            async with amqp_message.process():
                yield decodes(amqp_message.body.decode('utf-8'))

    async def handle_message(self, message_in: Message, channel_pool: aio_pika.pool.Pool):
        try:
            async for message_out in self.do_work(message_in):
                message = aio_pika.Message(body=encodes(message_out).encode('utf-8'))
                routing_key = str(PubTopic(message_out.key))
                await self.publish(message, routing_key, channel_pool)
        except Exception as err:  # pylint: disable=broad-except
            message_in.error = make_error_output(err)
            message_in.traceback = str(err)
            message = aio_pika.Message(body=jsons.dumps(message_in).encode('utf-8'))
            routing_key = f'{self.component_queue_name}_error'
            await self.publish(message, routing_key, channel_pool)

    async def publish(self, message: aio_pika.Message, routing_key: str, channel_pool: aio_pika.pool.Pool) -> None:
        """
        Re-acquires handles to `channel`, `exchange`, and `queue` before publishing message.

        Parameters:
            message: Message to be published
            routing_key: Exchange-level routing discriminator
            channel_pool: aio_pika.pool.Pool
        """
        async with channel_pool.acquire() as channel:
            exchange = await channel.get_exchange(name=self.exchange_name, ensure=False)
            await exchange.publish(message, routing_key)

    @aiomisc.threaded_iterable_separate
    def do_work(self, data_in: Message) -> AsyncIterable[Message]:
        """
        Performs the potentially long-running work of `self._invocable.invoke` in a separate thread
        within the constraints of the underlying execution context.

        Parameters:
            data_in: Raw event data

        Yields:
            message: Lazily-evaluable wrapper around return values from `self._invocable.invoke`, plus metadata
        """
        yield from self.invoke_handler(data_in)
