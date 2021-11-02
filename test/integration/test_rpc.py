import pytest
from test.integration.utils import ergo
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from ergo_python.rpc_client import ErgoRPCClient
from ergo_python.config import Namespace


BROKER_URL = "amqp://guest:guest@localhost:5672/%2F"


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
        "protocol": "amqp",
        "host": BROKER_URL,
        "subtopic": "product.in",
        "pubtopic": "product.out",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        namespace = Namespace(dict(**manifest, **namespace))
        rpc_client = ErgoRPCClient(namespace)
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

    do_twice_manifest = {"func": f"{__file__}:do_twice", "protocol": "amqp"}
    bedazzle_manifest = {"func": f"{__file__}:bedazzle", "protocol": "amqp"}
    do_twice_namespace = {"subtopic": "do_twice", "pubtopic": "do_twice_pub", "host": BROKER_URL}
    bedazzle_namespace = {"subtopic": "do_twice_pub", "pubtopic": "bedazzle", "host": BROKER_URL}
    with ergo("start", manifest=do_twice_manifest, namespace=do_twice_namespace):
        with ergo("start", manifest=bedazzle_manifest, namespace=bedazzle_namespace):
            rpc_namespace = Namespace({"subtopic": "do_twice", "pubtopic": "bedazzle"})
            rpc_client = ErgoRPCClient(rpc_namespace)
            result = rpc_client.call(statement="bedazzle me")
            for _ in range(2):
                assert next(result) == "🌟 bedazzle me 🌟"
