import pytest
import pika
import pika.exceptions
import json
from test.integration.utils import ergo, retries
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from src.topic import PubTopic, SubTopic


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"
EXCHANGE = "test_rpc_exchange"


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()


def product(x, y):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    manifest = {
        "func": f"{__file__}:product",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": EXCHANGE,
        "subtopic": "product.in",
        "pubtopic": "product.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = json.dumps({"data": {"x": 4, "y": 5}})
        result = next(rpc_call(payload, **manifest, **namespace))
        assert result == 20.0


def get_dict():
    return {"key": "value"}


def get_two_dicts():
    return [get_dict(), get_dict()]


def test_get_two_dicts(rabbitmq):
    manifest = {
        "func": f"{__file__}:get_two_dicts",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": EXCHANGE,
        "subtopic": "get_two_dicts.in",
        "pubtopic": "get_two_dicts.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = '{"data": {}}'
        results = rpc_call(payload, **manifest, **namespace)
        assert next(results) == get_two_dicts()


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


def test_yield_two_dicts(rabbitmq):
    manifest = {
        "func": f"{__file__}:yield_two_dicts",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": EXCHANGE,
        "subtopic": "yield_two_dicts.in",
        "pubtopic": "yield_two_dicts.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = '{"data": {}}'
        results = rpc_call(payload, **manifest, **namespace)
        assert next(results) == get_dict()
        assert next(results) == get_dict()


def rpc_call(payload, func, host, exchange, pubtopic, subtopic, **_):
    connection = pika.BlockingConnection(pika.URLParameters(host))
    for retry in retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()
            channel.exchange_declare(exchange, passive=True)
            error_channel = connection.channel()
            error_channel.queue_purge(queue=f"{func}_error")

    queue_name = f"{func}_rpc"
    channel.queue_declare(queue=queue_name)
    channel.queue_purge(queue_name)
    channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=str(SubTopic(pubtopic)))

    publish(host, exchange, subtopic, payload)

    while True:
        _, _, body = next(error_channel.consume(f"{func}_error", inactivity_timeout=0.1))
        if body:
            raise RuntimeError(json.loads(body)["error"])
        _, _, body = next(channel.consume(queue_name, inactivity_timeout=0.1))
        if body:
            yield json.loads(body)["data"]


def publish(host, exchange, routing_key, payload: str):
    connection = pika.BlockingConnection(pika.URLParameters(host))
    channel = connection.channel()
    try:
        # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
        # of the dead letter queue.
        channel.confirm_delivery()
        for retry in retries(10, 0.5, pika.exceptions.UnroutableError):
            with retry():
                channel.basic_publish(exchange=exchange, routing_key=str(PubTopic(routing_key)), body=payload, mandatory=True)
    finally:
        channel.close()
        connection.close()
