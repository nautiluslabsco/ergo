import json

import aio_pika
from aio_pika.exchange import ExchangeType

from src.amqp_invoker import AmqpInvoker
from src.types import TYPE_PAYLOAD


class RPCInvoker(AmqpInvoker):
    exchange_type = ExchangeType.DIRECT

    @property
    def routing_key(self) -> str:
        return self._invocable.config.rpc_routing_key

    async def on_message(
        self, message: aio_pika.IncomingMessage, channel: aio_pika.RobustChannel
    ) -> None:
        """
        Primary event queue callback.

        Parameters:
            message: Message object with convenience methods for acknowledgement
            channel: Connection handle and state
        """

        # `message.process` will call `message.ack` upon `__aexit__` or `__exit__` (since no additional flags are passed to it),
        # as well as handle requeueing and rejects if there are failures
        async with message.process():
            data_in: TYPE_PAYLOAD = dict(json.loads(message.body.decode("utf-8")))
            try:
                # `self.do_work` is guaranteed to run on a separate thread, which is recommended for potentially long-running background tasks
                async with self.do_work(data_in) as generator:
                    async for data_out in generator:
                        out_message = aio_pika.Message(
                            body=json.dumps(data_out).encode(),
                            correlation_id=message.correlation_id,
                        )
                        await channel.default_exchange.publish(
                            message=out_message,
                            routing_key=message.reply_to,
                        )

            except Exception as err:  # pylint: disable=broad-except
                data_in["error"] = str(err)
                # TODO(ahuman-bean): cleaner error messages
                out_message = aio_pika.Message(
                    body=json.dumps(data_in).encode(),
                    correlation_id=message.correlation_id,
                )
                await channel.default_exchange.publish(
                    message=out_message, routing_key=message.reply_to
                )
