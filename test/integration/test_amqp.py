import pytest
import subprocess
import pika
import unittest
import asyncio
import json
import functools
import docker
import time
import requests
import multiprocessing
from typing import Dict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pika import URLParameters, BlockingConnection
from src.ergo_cli import ErgoCli
from src.amqp_invoker import declare_topic_exchange
from test.integration.scaffold import ErgoStartTest
from urllib.parse import urlencode


# AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F?connection_attempts=5&retry_delay=.1"
# AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F?heartbeat=1"
AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session", autouse=True)
def rabbitmq():
    result = subprocess.run(["docker-compose", "up", "-d", "rabbitmq"])
    # assert result.returncode == 0
    docker_client = docker.from_env()
    container, = docker_client.containers.list(filters={"name": "rabbitmq"})
    # container, = docker_client.containers.list()
    # container = docker_client.containers.run(
    #     name="rabbitmq",
    #     image="rabbitmq:3.8.16-management-alpine",
    #     ports={5672: 5672},
    #     detach=True,
    # )

    print("awaiting broker")
    output = ""
    for retry in range(200):
        if container.status == "running":
            exit_code, output = container.exec_run(["rabbitmqctl", "await_online_nodes", "1"])
            if exit_code == 0:
                break
        time.sleep(.5)
    else:
        raise RuntimeError(output)
    print("broker started")
    bh = True

#
#
# def teardown_module():
#     subprocess.run(["docker-compose", "down", "-v"])


def publish(routing_key: str, data: Dict, exchange_name: str):
    parameters = URLParameters(AMQP_HOST)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange_name, exchange_type='topic', passive=False, durable=True,
                             auto_delete=False, internal=False, arguments=None)
    channel.basic_publish(exchange=exchange_name, routing_key=ergo_compliant(routing_key), body=json.dumps(data))  # noqa
    channel.close()
    connection.close()


# TODO do we want to use this here?
def ergo_compliant(routing_key: str) -> str:
    """
    ergo likes to alphanumerically sort the subkeys in a routing key.
    This is so that an arbitrary subkey can be inserted w/ out disturbing overall routing.
    :param routing_key:
    :return:
    """
    return '.'.join(sorted(
       routing_key.split('.')
    ))


class TestStartProduct0(unittest.IsolatedAsyncioTestCase):
    manifest = "configs/product.yml"
    namespace = "configs/amqp.yml"

    async def runTest(self):
        data = {"data": '{"x": 4, "y": 5}'}
        # publish("product_in", data, "primary")

        def on_open(connection):
            connection.channel(on_open_callback=functools.partial(on_channel_open, connection))

        def on_channel_open(connection, channel):
            channel.exchange_declare("primary", exchange_type='topic', passive=False, durable=True,
                                     auto_delete=False, internal=False, arguments=None)
            add_consumer(connection, channel, "product_out", consume_callback)
            add_consumer(connection, channel, "product_in", mock_callback)
            print("publishing")
            channel.basic_publish(exchange="primary", routing_key=ergo_compliant("product_in"),
                                  body=json.dumps(data))  # noqa
            print("published")
            assert False

        def consume_callback(channel, body):
            print("inside consume_callback")
            result = body["data"]
            self.assertEqual(20.1, result)

        def mock_callback(channel, body):
            channel.basic_publish(exchange="primary", routing_key=ergo_compliant("product_out"), body="{}")

        def consume_error_callback(channel, body):
            print("inside consume_error_callback")
            body = json.loads(body)
            error = body["error"]
            raise Exception(error)

        def add_consumer(connection, channel, queue_name, consumer):
            channel.queue_declare(queue=queue_name)
            channel.queue_bind(exchange="primary", queue=queue_name)
            channel.queue_purge(queue_name)

            def on_message_callback(chan, method, properties, body):
                connection.ioloop.stop()
                body = json.loads(body)
                consumer(channel, body)

            print(f"adding {queue_name} consumer")
            channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)
            print(f"added {queue_name} consumer")


        connection = pika.SelectConnection(URLParameters(AMQP_HOST), on_open_callback=on_open)

        connection.ioloop.start()


class TestStartProduct(ErgoStartTest, unittest.IsolatedAsyncioTestCase):
    manifest = "configs/product.yml"
    namespace = "configs/amqp.yml"

    def runTest(self):

        def on_open(connection):
            connection.channel(on_open_callback=on_channel_open)

        def on_channel_open(channel):
            data = {"data": '{"x": 4, "y": 5}'}
            channel.exchange_declare("primary", exchange_type='topic', passive=False, durable=True,
                                     auto_delete=False, internal=False, arguments=None)
            print("publishing")
            channel.basic_publish(exchange="primary", routing_key=ergo_compliant("product_in"),
                                  body=json.dumps(data))  # noqa
            add_consumer("product_out", consume, channel)
            # add_consumer("entrypoints.py:product_error", consume_error, channel)

        def add_consumer(queue_name, consumer, channel):
            channel.queue_declare(queue=queue_name)
            channel.queue_bind(exchange="primary", queue=queue_name)
            channel.queue_purge(queue_name)

            def wrapped(method, properties, body):
                print(f"{queue_name} consumer consumed")
                channel.stop_consuming()
                return consumer(body)

            print(f"adding {queue_name} consumer")
            channel.basic_consume(queue=queue_name, on_message_callback=wrapped)
            print(f"added {queue_name} consumer")

        def consume(body):
            print("inside consume")
            body = json.loads(body)
            result = body["data"]
            self.assertEqual(20.0, result)

        def consume_error(body):
            print("inside consume_error")
            body = json.loads(body)
            error = body["error"]
            raise Exception(error)

        connection = pika.SelectConnection(URLParameters(AMQP_HOST), on_open_callback=on_open)
        try:
            print("blocking")
            connection.ioloop.start()
        except:
            connection.close()

    def foo(self):
        print("publishing")
        publish("product_in", {"data": '{"x": 4, "y": 5}'}, "primary")
        print("published")

        connection = pika.BlockingConnection(URLParameters(AMQP_HOST))
        channel = connection.channel()

        def add_consumer(queue_name, consumer):
            channel.queue_declare(queue=queue_name)
            channel.queue_bind(exchange="primary", queue=queue_name)
            channel.queue_purge(queue_name)

            def wrapped(*args, **kwargs):
                channel.stop_consuming()
                return consumer(*args, **kwargs)

            channel.basic_consume(queue=queue_name, on_message_callback=wrapped)

        def consume(channel, method, properties, body):
            result = body["data"]
            self.assertEqual(20.0, result)

        def consume_error(channel, method, properties, body):
            error = body["error"]
            raise Exception(error)

        add_consumer("product_out", consume)
        add_consumer("entrypoints.py:product_error", consume_error)

        print("test consuming")
        channel.start_consuming()


class TestStartProduct2(ErgoStartTest, unittest.IsolatedAsyncioTestCase):
    manifest = "configs/product.yml"
    namespace = "configs/amqp.yml"

    async def runTest(self):
        print("publishing")
        publish("product_in", {"data": '{"x": 4, "y": 5}'}, "primary")

        def consume_callback(body):
            result = body["data"]
            self.assertEqual(20.1, result)

        def consume_error_callback(body):
            error = body["error"]
            raise Exception(error)

        error = add_consumer("entrypoints.py:product_error", consume_error_callback)
        await add_consumer("product_out", consume_callback)

        # loop = asyncio.get_event_loop()
        # done, pending = await asyncio.wait([add_consumer("entrypoints.py:product_error", consume_error_callback)], timeout=1)
        # for task in pending:
        #     task.cancel()

        # await asyncio.wait([add_consumer("product_out", consume_callback)], timeout=1)
        # await error
        # await add_consumer("product_out", consume_callback)


async def add_consumer(queue_name, on_message_callback):
    connection = pika.BlockingConnection(URLParameters(AMQP_HOST))
    channel = connection.channel()
    # channel.basic_qos(prefetch_count=1)
    print(f"adding {queue_name} consumer")
    channel.queue_declare(queue=queue_name)
    channel.queue_bind(exchange="primary", queue=queue_name)
    channel.queue_purge(queue_name)
    _, _, body = next(channel.consume(queue_name))
    body = json.loads(body)
    print(f"{queue_name} consumer consumed")
    ret = on_message_callback(body)
    channel.close()
    return ret


class TestStartProduct3(ErgoStartTest, unittest.IsolatedAsyncioTestCase):
    manifest = "configs/product.yml"
    namespace = "configs/amqp.yml"

    async def runTest(self):
        # print("publishing")
        # publish("product_in", {"data": '{"x": 4, "y": 5}'}, "primary")

        connection = pika.BlockingConnection(URLParameters(AMQP_HOST))
        channel = connection.channel()
        declare_topic_exchange(channel, "primary")

        def consume_callback(body):
            print("inside consume_callback")
            result = body["data"]
            self.assertEqual(20.1, result)

        def consume_error_callback(body):
            print("inside consume_error_callback")
            error = body["error"]
            raise Exception(error)

        def add_consumer(queue_name, consumer):
            channel.queue_declare(queue=queue_name)
            channel.queue_bind(exchange="primary", queue=queue_name)
            channel.queue_purge(queue_name)

            def on_message_callback(chan, method, properties, body):
                channel.stop_consuming()
                body = json.loads(body)
                return consumer(body)

            channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)


        add_consumer("product_out", consume_callback)
        add_consumer("entrypoints.py:product_error", consume_error_callback)

        print("publishing")
        channel.confirm_delivery()
        err = None
        for retry in range(5):
            try:
                data = {"data": '{"x": 4, "y": 5}'}
                channel.basic_publish(exchange="primary", routing_key=ergo_compliant("product_in"),
                                      body=json.dumps(data), mandatory=True)  # noqa
                break
            except pika.exceptions.UnroutableError as err:
                import time
                time.sleep(.5)
        else:
            raise err

        channel.start_consuming()
