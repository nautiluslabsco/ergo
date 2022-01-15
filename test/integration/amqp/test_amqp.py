from test.integration.amqp.utils import ComponentFailure, AMQPComponent
import pytest
from ergo.context import Context


def product(x, y=1):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    with AMQPComponent(product) as component:
        result = component.rpc({"x": 4, "y": 5})
        assert result["data"] == 20.0


class Product:
    @classmethod
    def __call__(cls, x, y):
        return x * y


def test_product_class(rabbitmq):
    with AMQPComponent(Product) as component:
        result = component.rpc({"x": 4, "y": 5})
        assert result["data"] == 20.0


def get_dict():
    return {"key": "value"}


def get_two_dicts():
    return [get_dict(), get_dict()]


def test_get_two_dicts(rabbitmq):
    with AMQPComponent(get_two_dicts) as component:
        result = component.rpc({})
        assert result["data"] == get_two_dicts()


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


def test_yield_two_dicts(rabbitmq):
    with AMQPComponent(yield_two_dicts) as component:
        component.send({})
        assert component.consume()["data"] == get_dict()
        assert component.consume()["data"] == get_dict()


def assert_false():
    assert False


def test_error_path(rabbitmq):
    with AMQPComponent(assert_false) as component:
        with pytest.raises(ComponentFailure):
            component.send({})
            component.propagate_error()


def make_six(context: Context):
    context.pubtopic = "forward"
    return {"recipient": "double_in", "x": 3}


def forward(context, data):
    context.pubtopic = data.pop("recipient")
    return data


def double(x: float):
    return 2 * x


def test_make_six(rabbitmq):
    with AMQPComponent(make_six, subtopic="make_six") as make_six_component:
        with AMQPComponent(forward, subtopic="forward") as forward_component:
            with AMQPComponent(double, subtopic="double_in", pubtopic="double_out") as double_component:
                make_six_component.send({})
                result = double_component.consume()
                if not result:
                    make_six_component.propagate_error(inactivity_timeout=0.1)
                    forward_component.propagate_error(inactivity_timeout=0.1)
                assert result["data"] == 6


def outer_transaction(context):
    assert len(context._transaction_stack) == 0
    context.open_transaction()
    assert len(context._transaction_stack) == 1
    return True


def inner_transaction(context):
    assert len(context._transaction_stack) == 0
    context.open_transaction()
    return True


def test_transaction(rabbitmq):
    with AMQPComponent(inner_transaction, subtopic="outer_transaction_pub") as inner_transaction_component:
        with AMQPComponent(outer_transaction, pubtopic="outer_transaction_pub") as outer_transaction_component:
            outer_transaction_component.send({})
            inner_txn_result = inner_transaction_component.consume()
            outer_txn_result = outer_transaction_component.consume()

            outer_txn_stack = outer_txn_result["metadata"]["transaction_stack"]
            assert len(outer_txn_stack) == 1
            inner_txn_stack = inner_txn_result["metadata"]["transaction_stack"]
            assert len(inner_txn_stack) == 2
            assert inner_txn_stack[0] == outer_txn_stack[0]
