import pytest
import pika
import json
import docker
import time
import timeout_decorator
from contextlib import contextmanager
from test.integration.utils import ergo
from src.topic import PubTopic, SubTopic


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
    for retry in _retries(200, 0.5, pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
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
        result = rpc(json.dumps({"data": {"x": 4, "y": 5}}), **manifest, **namespace)
        assert result == 20.0


@timeout_decorator.timeout(seconds=2)
def rpc(payload, **config):
    ret = {}

    connection = pika.BlockingConnection(pika.URLParameters(config["host"]))
    for retry in _retries(20, 0.5, pika.exceptions.ChannelClosedByBroker, pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()
            channel.exchange_declare(config["exchange"], passive=True)

    def on_pubtopic_message(body):
        result = body["data"]
        ret["result"] = result

    def on_error_mesage(body):
        error = body["error"]
        ret["error"] = error

    def add_consumer(queue_name, consumer):
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=config["exchange"], queue=queue_name)
        channel.queue_purge(queue_name)

        def on_message_callback(chan, method, properties, body):
            channel.stop_consuming()
            body = json.loads(body)
            return consumer(body)

        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)

    add_consumer(str(PubTopic(config["pubtopic"])), on_pubtopic_message)
    add_consumer(f"{config['func']}_error", on_error_mesage)

    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in _retries(10, 0.5, pika.exceptions.UnroutableError):
        with retry():
            channel.basic_publish(exchange=config["exchange"], routing_key=str(SubTopic(config["subtopic"])),
                                  body=payload, mandatory=True)  # noqa

    try:
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()

    if ret.get("error"):
        raise Exception(ret["error"])
    return ret["result"]


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
            except Exception as e:
                raise


        yield retry
