"""Summary."""
import aio_pika
import aiomisc
import asyncio
import json

from retry import retry
from typing import Awaitable, Callable, Iterable
from urllib.parse import urlparse

from src.function_invocable import FunctionInvocable
from src.invoker import Invoker
from src.types import TYPE_PAYLOAD

# content_type: application/json
# {"x":5,"y":7}

# TODO(ahuman-bean): requires fine-tuning
MAX_THREADS = 2


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

    def start(self) -> int:
        """
        Starts a new event loop that maintains a persistent AMQP connection.
        Underlying execution context is a thread pool of size `MAX_THREADS`.
        """
        loop = aiomisc.new_event_loop(pool_size=MAX_THREADS)
        connection = loop.run_until_complete(self.run(loop))

        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(connection.close())
        
        return 0

    @retry(aio_pika.exceptions.AMQPConnectionError, delay=1, jitter=(1, 3), backoff=2)
    async def run(self, loop: asyncio.AbstractEventLoop) -> aio_pika.RobustConnection:
        """
        Establishes the AMQP connection with rudimentary retry logic on `aio_pika.exceptions.AMQPConnectionError`.
        Consumer workers run in separate tasks against a single read/write channel.

        Parameters:
            loop: Asyncio-compliant event loop primitive that is responsible for scheduling work

        Returns:
            connection: Connection that attempts to restore state (channels, queues, etc.) upon reconnects
        """
        connection = await aio_pika.connect_robust(url=self.url, loop=loop)

        async with connection:
            async with connection.channel() as channel:
                try:
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

                    futures = [
                        self.consume(channel, queue, self.on_message),
                        # TODO(ahuman-bean): implement error handling
                        # self.consume(channel, queue_error, self.on_error)
                    ]

                    await asyncio.gather(*futures)
                except KeyboardInterrupt:
                    loop.run_until_complete(channel.close())
                except aio_pika.exceptions.ConnectionClosed:
                    pass

        return connection

    async def consume(
        self,
        channel: aio_pika.RobustChannel,
        queue: aio_pika.RobustQueue,
        callback: Callable[[aio_pika.IncomingMessage, aio_pika.RobustChannel], Awaitable[None]]
    ):
        """
        Binds a single consumer tag to `queue` and continuously pulls `message`s into `callback`.

        Parameters:
            channel: Connection state
            queue: Queue from which to read
            callback: Awaitable callback
        """
        async with queue.iterator() as consumed:
            async for message in consumed:
                await callback(message, channel)
                await message.ack()

    async def on_message(self, message: aio_pika.IncomingMessage, channel: aio_pika.RobustChannel):
        """
        Primary event queue callback.

        Parameters:
            message: Message object with convenience methods for acknowledgement
            channel: Connection state
        """
        async with message.process():
            data_in: TYPE_PAYLOAD = dict(json.loads(message.body.decode('utf-8')))
            exchange = await channel.get_exchange(self._invocable.config.exchange)

            try:
                async with self.do_work(data_in) as generator:
                    async for data_out in generator:
                        await exchange.publish(message=aio_pika.Message(body=json.dumps(data_out).encode()), routing_key=str(self._invocable.config.pubtopic))

            except Exception as err:  # pylint: disable=broad-except
                data_in['error'] = str(err)
                # TODO(ahuman-bean): cleaner error messages
                await exchange.publish(message=aio_pika.Message(body=json.dumps(data_in).encode()), routing_key=f'{self.queue_name}_error')

    async def on_error(message: aio_pika.IncomingMessage, channel: aio_pika.RobustChannel):
        """
        Stub for an error queue callback.

        Parameters:
            message: Message object with convenience methods for acknowledgement
            channel: Connection state
        """
        pass

    @aiomisc.threaded_iterable
    def do_work(self, data_in: TYPE_PAYLOAD) -> Iterable[TYPE_PAYLOAD]:
        """
        Performs the potentially CPU-intensive work of `self._invocable.invoke` in a separate thread
        within the constraints of the underlying execution context.

        Parameters:
            data_in: Raw event data

        Returns:
            payload: Lazily-evaluable wrapper around return values from `self._invocable.invoke`
        """
        for data_out in self._invocable.invoke(data_in["data"]):
            yield {
                "data": data_out,
                "key": str(self._invocable.config.pubtopic),
                "log": data_in.get("log", [])
            }
