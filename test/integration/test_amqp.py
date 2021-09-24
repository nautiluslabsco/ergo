import pytest
import pika
import json
import docker
import time
import timeout_decorator
from pika import URLParameters
from src.amqp_invoker import declare_topic_exchange
from src.config import Config
from test.integration.utils import with_ergo


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session")
def rabbitmq():
    """
    Start a rabbitmq docker container if none is running, and then wait for the broker to finish booting.
    """
    docker_client = docker.from_env()
    try:
        container, = docker_client.containers.list(filters={"name": "rabbitmq"})
    except ValueError:
        container = docker_client.containers.run(
            name="rabbitmq",
            image="rabbitmq:3.8.16-management-alpine",
            ports={5672: 5672},
            detach=True,
        )

    print("awaiting broker")
    output = ""
    for retry in range(200):
        try:
            exit_code, output = container.exec_run(["rabbitmqctl", "await_online_nodes", "1"])
            if exit_code == 0:
                break
        except docker.errors.APIError:
            pass
        time.sleep(.5)
    else:
        raise RuntimeError(output)
    print("broker started")


@with_ergo("start", f"test/integration/configs/product.yml", "test/integration/configs/amqp.yml")
def test_product_amqp(rabbitmq):
    conf = Config({
        "func": "test/integration/target_functions.py:product",
        "exchange": "primary",
        "subtopic": "product.in",
        "pubtopic": "product.out",
    })
    result = ergo_rpc({"x": 4, "y": 5}, conf)
    assert result == 20.0


@with_ergo("start", f"test/integration/configs/product.yml", "test/integration/configs/amqp.yml")
def test_product_amqp__legacy(rabbitmq):
    conf = Config({
        "func": "test/integration/target_functions.py:product",
        "exchange": "primary",
        "subtopic": "product.in",
        "pubtopic": "product.out",
    })
    result = ergo_rpc({"data": '{"x": 4, "y": 5}'}, conf)
    assert result == 20.0


@timeout_decorator.timeout(seconds=2)
def ergo_rpc(payload, config: Config):
    ret = {}

    connection = pika.BlockingConnection(URLParameters(AMQP_HOST))
    channel = connection.channel()
    declare_topic_exchange(channel, config.exchange)

    def on_pubtopic_message(body):
        result = body["data"]
        ret["result"] = result

    def on_error_mesage(body):
        error = body["error"]
        ret["error"] = error

    def add_consumer(queue_name, consumer):
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=config.exchange, queue=queue_name)
        channel.queue_purge(queue_name)

        def on_message_callback(chan, method, properties, body):
            channel.stop_consuming()
            body = json.loads(body)
            return consumer(body)

        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)

    add_consumer(str(config.pubtopic), on_pubtopic_message)
    add_consumer(f"{config.func}_error", on_error_mesage)

    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    err = None
    for retry in range(10):
        try:
            routing_key = str(config.subtopic)
            channel.basic_publish(exchange=config.exchange, routing_key=routing_key,
                                  body=json.dumps(payload), mandatory=True)  # noqa
            break
        except pika.exceptions.UnroutableError as err:
            time.sleep(.05)
    else:
        raise err

    try:
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()

    if ret.get("error"):
        raise Exception(ret["error"])
    return ret["result"]
