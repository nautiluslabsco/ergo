import pytest
import pika
import json
import docker
import time
from contextlib import contextmanager
from test.integration.utils import ergo
from ergo.topic import PubTopic, SubTopic


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session")
def rabbitmq():
    """
    Start a rabbitmq server if none is running, and then wait for the broker to finish booting.
    """
    docker_client = docker.from_env()
    if not docker_client.containers.list(filters={"name": "rabbitmq"}):
        docker_client.containers.run(
            name="rabbitmq",
            image="rabbitmq:3.8.16-management-alpine",
            ports={5672: 5672, 15672: 15672},
            detach=True,
        )

    print("awaiting broker")
    for retry in _retries(200, 0.5, pika.exceptions.AMQPConnectionError):
        with retry():
            pika.BlockingConnection(pika.URLParameters(AMQP_HOST))
    print("broker started")


def product(x, y):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    manifest = {
        "func": f"{__file__}:product",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "subtopic": "product.in",
        "pubtopic": "product.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = json.dumps({"x": 4, "y": 5})
        result = next(rpc(payload, **manifest, **namespace))
        assert result == {'data': 20.0, 'key': 'out.product', 'log': []}


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
        "exchange": "test_exchange",
        "subtopic": "get_two_dicts.in",
        "pubtopic": "get_two_dicts.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = '{"data": {}}'
        results = rpc(payload, **manifest, **namespace)
        expected = {
            'data': get_two_dicts(),
            'key': 'get_two_dicts.out',
            'log': []
        }
        assert next(results) == expected


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
        "exchange": "test_exchange",
        "subtopic": "yield_two_dicts.in",
        "pubtopic": "yield_two_dicts.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        payload = '{"data": {}}'
        results = rpc(payload, **manifest, **namespace)
        expected = {
            'data': get_dict(),
            'key': 'out.yield_two_dicts',
            'log': []
        }
        assert next(results) == expected
        assert next(results) == expected


def assert_false():
    assert False


def test_error_path(rabbitmq):
    manifest = {
        "func": f"{__file__}:assert_false",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "subtopic": "assert_false.in",
        "pubtopic": "assert_false.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        with pytest.raises(ComponentFailure):
            next(rpc("{}", **manifest, **namespace))


def rpc(payload, func, host, exchange, pubtopic, subtopic, **_):
    connection = pika.BlockingConnection(pika.URLParameters(host))
    for retry in _retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
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
            raise ComponentFailure(json.loads(body)["error"])
        _, _, body = next(channel.consume(queue_name, inactivity_timeout=0.1))
        if body:
            yield json.loads(body)


def publish(host, exchange, routing_key, payload: str):
    connection = pika.BlockingConnection(pika.URLParameters(host))
    channel = connection.channel()
    try:
        # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
        # of the dead letter queue.
        channel.confirm_delivery()
        for retry in _retries(10, 0.5, pika.exceptions.UnroutableError):
            with retry():
                channel.basic_publish(exchange=exchange, routing_key=str(PubTopic(routing_key)), body=payload, mandatory=True)
    finally:
        channel.close()
        connection.close()


def _retries(n: int, backoff_seconds: float, *retry_errors: BaseException):
    retry_errors = retry_errors or (Exception,)

    success = set()
    for attempt in range(n):
        if success:
            break

        @contextmanager
        def retry():
            try:
                yield
                success.add(True)
            except retry_errors:
                if attempt+1 == n:
                    raise
                time.sleep(backoff_seconds)

        yield retry


class ComponentFailure(BaseException):
    pass
