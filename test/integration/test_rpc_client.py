import pytest
from test.integration.utils import ergo
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from ergo_python.rpc_client import ErgoRPCClient
from ergo_python.config import Graph


BROKER_URL = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()


def product(x, y):
    return float(x) * float(y)


def test_product_rpc(rabbitmq):
    config = {
        "func": f"{__file__}:product",
        "subtopic": "product.in",
        "pubtopic": "product.out",
        "protocol": "amqp",
        "host": BROKER_URL,
    }
    with ergo("start", manifest=config):
        graph = Graph(config)
        rpc_client = ErgoRPCClient(graph)
        result = next(rpc_client.call(x=4, y=5))
        assert result == 20.0

        # test unexpected argument
        with pytest.raises(RuntimeError):
            next(rpc_client.call(x=4, y=5, z=6))


def do_twice(**kwargs):
    for _ in range(2):
        yield kwargs


def bedazzle(statement):
    return f"🌟 {statement} 🌟"


def test_bedazzle(rabbitmq):
    """
    assert that ErgoRPCClient can synchronously return data passed through multiple components
    """

    do_twice_manifest = {
        "func": f"{__file__}:do_twice",
        "protocol": "amqp",
        "host": BROKER_URL,
        "subtopic": "do_twice",
        "pubtopic": "do_twice_pub",
    }
    bedazzle_manifest = {
        "func": f"{__file__}:bedazzle",
        "protocol": "amqp",
        "host": BROKER_URL,
        "subtopic": "do_twice_pub",
        "pubtopic": "bedazzle",
    }
    with ergo("start", manifest=do_twice_manifest):
        with ergo("start", manifest=bedazzle_manifest):
            graph = Graph({"subtopic": "do_twice", "pubtopic": "bedazzle"})
            rpc_client = ErgoRPCClient(graph)
            result = rpc_client.call(statement="bedazzle me")
            for _ in range(2):
                assert next(result) == "🌟 bedazzle me 🌟"
