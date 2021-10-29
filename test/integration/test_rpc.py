import pytest
import pika
import pika.exceptions
import json
from test.integration.utils import ergo, retries
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from typing import Optional, Dict
import uuid


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "test_rpc_exchange"


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()


def product(x, y):
    return float(x) * float(y)


def test_product_rpc(rabbitmq):
    manifest = {
        "func": f"{__file__}:product",
    }
    namespace = {
        "protocol": "rpc",
        "host": AMQP_HOST,
        "exchange": EXCHANGE,
        "rpc_routing_key": "rpc_product"
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = {"x": 4, "y": 5}
        result = rpc_call(AMQP_HOST, namespace["exchange"], namespace["rpc_routing_key"], payload)
        assert result == 20.0


def test_product_rpc__unexpected_argument(rabbitmq):
    manifest = {
        "func": f"{__file__}:product",
    }
    namespace = {
        "protocol": "rpc",
        "host": AMQP_HOST,
        "exchange": EXCHANGE,
        "rpc_routing_key": "rpc_product"
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = {"x": 4, "y": 5, "z": 6}
        with pytest.raises(RuntimeError):
            rpc_call(AMQP_HOST, namespace["exchange"], namespace["rpc_routing_key"], payload)


def rpc_call(broker: str, exchange: str, routing_key: str, payload: Optional[Dict] = None):
    connection = pika.BlockingConnection(pika.URLParameters(broker))

    for retry in retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()
            channel.exchange_declare(EXCHANGE, passive=True)

    callback_queue = channel.queue_declare(
        queue="",
        auto_delete=True
    ).method.queue

    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in retries(10, 0.5, pika.exceptions.UnroutableError):
        with retry():
            body = json.dumps({"data": payload or {}})
            correlation_id = str(uuid.uuid4())
            properties = pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=correlation_id,
            )
            channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body, properties=properties,
                                  mandatory=True)

    for _, props, body in channel.consume(callback_queue):
        if props.correlation_id != correlation_id:
            continue
        message = json.loads(body)
        if "error" in message:
            raise RuntimeError(message["error"])
        return message["data"]
