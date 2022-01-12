import json
from test.integration.amqp.utils import publish, AMQP_HOST, ComponentFailure, AMQPComponent
from test.integration.utils import ergo, retries
import pika
import pika.exceptions
import pytest
from ergo.topic import SubTopic




# class Product:
#     def __call__(self, x, y=1):
#         pass
#
# product = Product()


def product(x, y=1):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    component = AMQPComponent(product, subtopic="product.in", pubtopic="product.out")
    with component.start():
        result = next(component.rpc(x=4, y=5))
        assert result["data"] == 20.0


def return_three():
    return 3


def double_three(context, data: float):
    return 2 * data


def test_make_six(rabbitmq):
    return_three_manifest = {
        "func": f"{__file__}:return_three",
    }
    return_three_namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "subtopic": "return_six.in",
        "pubtopic": "double_three.in",
    }
    double_three_manifest = {
        "func": f"{__file__}:double_three",
    }
    double_three_namespace = {
        "protocol": "amqp",
        "host": AMQP_HOST,
        "exchange": "test_exchange",
        "subtopic": "double_three.in",
        "pubtopic": "return_six.out",
    }
    with ergo("start", manifest=return_three_manifest, namespace=return_three_namespace):
        with ergo("start", manifest=double_three_manifest, namespace=double_three_namespace):
            kwargs = {**double_three_manifest, **double_three_namespace}
            kwargs.update({"subtopic": "return_six.in", "pubtopic": "return_six.out"})
            result = next(rpc("{}", **kwargs))
        assert result == {'data': 6, 'key': 'out.return_six', 'log': []}


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

    publish(subtopic, payload)

    while True:
        _, _, body = next(error_channel.consume(f"{func}_error", inactivity_timeout=0.1))
        if body:
            raise ComponentFailure(json.loads(body)["error"])
        _, _, body = next(channel.consume(queue_name, inactivity_timeout=0.1))
        if body:
            yield json.loads(body)


