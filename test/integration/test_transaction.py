from collections import defaultdict
from test.integration.utils import ergo, retries
from ergo.config import Config
from typing import Optional, Iterator, Callable, NewType, Dict, List, TypedDict
from contextlib import contextmanager
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
import pytest
import pika
import pika.exceptions
import json
from ergo.topic import PubTopic, SubTopic


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()


class Sandwich(TypedDict):
    meat: str
    cheese: str









def order_sandwich(toppings: Dict):
    # toppings is e.g. {"meat": "ham", "cheese": "havarti"}
    for topping, variety in toppings.items():
        yield {topping: variety}


def procure_topping(topping: Dict):
    process_topping(topping)  # noqa
    return topping


sandwich_db: Dict = defaultdict(dict)


def assemble_sandwich(context: Config, topping: Dict) -> Iterator:
    txn_id = context.transaction_id  # noqa
    sandwich = sandwich_db[txn_id]
    sandwich.update(topping)

    txn_data = context.transaction_data
    sandwich = txn_data["sandwich"]
    if "meat" in sandwich and "cheese" in sandwich:
        yield {"sandwich": sandwich_db.pop(txn_id)}











def is_assembled(sandwich: Sandwich) -> bool:
    if "order" not in sandwich:
        return False
    for topping in sandwich["order"]:
        if not sandwich.get(topping):
            return False
    return True


def test_order_sandwich(rabbitmq):
    with start_component(order_sandwich, "order_sandwich", "procure_topping"):
        with start_component(procure_topping, "procure_topping", "deliver_sandwich"):
            with start_component(procure_topping, "procure_topping", "deliver_sandwich"):
                with start_component(assemble_sandwich, "deliver_sandwich", "order_fulfilled"):
                    run_order_sandwich_test()


def run_order_sandwich_test():
    orders = [
        {"meat": "ham", "cheese": "havarti"},
        {"meat": None, "cheese": "pimento"},
        {"meat": "roast beef", "cheese": "mozzarella"},
    ]
    for order in orders:
        publish(AMQP_HOST, "test_exchange", "order_sandwich", json.dumps({"data": order}))
        bh = True

    connection = pika.BlockingConnection(pika.URLParameters(AMQP_HOST))
    for retry in retries(20, 0.5, pika.exceptions.ChannelClosedByBroker,
                         pika.exceptions.ChannelWrongStateError):
        with retry():
            channel = connection.channel()
            channel.exchange_declare("test_exchange", passive=True)
    queue_name = f"test_order_sandwich"
    channel.queue_declare(queue=queue_name)
    channel.queue_purge(queue_name)
    channel.queue_bind(exchange="test_exchange", queue=queue_name, routing_key=str(SubTopic("order_fulfilled")))

    results = []
    for _ in range(len(orders)):
        _, _, body = next(channel.consume(queue_name))
        results.append(json.loads(body)["data"])
    results = sorted(results, key=lambda row: orders.index(row) if row in orders else 0)
    assert results == orders


@contextmanager
def start_component(fn: Callable, subtopic: str, pubtopic: str):
    manifest = {
        "func": f"{__file__}:{fn.__name__}",
    }
    namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "subtopic": subtopic,
        "pubtopic": pubtopic,
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        yield


def rpc(func, host, exchange, pubtopic, subtopic, **_):
    generator = _rpc(func, host, exchange, pubtopic, subtopic)
    # generator.send(None)
    next(generator)
    return generator


def _rpc(func, host, exchange, pubtopic, subtopic, **_):
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

    payload = yield
    publish(host, exchange, subtopic, payload)

    while True:
        _, _, body = next(error_channel.consume(f"{func}_error", inactivity_timeout=0.1))
        if body:
            raise ComponentFailure(json.loads(body)["error"])
        _, _, body = next(channel.consume(queue_name, inactivity_timeout=0.1))
        if body:
            payload = yield json.loads(body)
            if payload:
                publish(host, exchange, subtopic, payload)


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


class ComponentFailure(BaseException):
    pass

