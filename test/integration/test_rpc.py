import pytest
from test.integration.utils import ergo
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from ergo_python.rpc_client import ErgoRPCClient
from ergo_python.config import Namespace


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
        "host": "amqp://guest:guest@localhost:5672/%2F",
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
