from test.integration.amqp.utils import AMQPComponent, ComponentFailure

import pytest

from ergo.context import Context


def product(x, y):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    with AMQPComponent(product) as component:
        result = component.rpc({"x": 4, "y": 5})
        assert result["data"] == 20.0


class Product:
    @classmethod
    def __call__(cls, x, y=2):
        return x * y


def test_product_class(rabbitmq):
    with AMQPComponent(Product) as component:
        result = component.rpc({"x": 4})
        assert result["data"] == 8.0


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


def upstream_transaction(context):
    context.open_transaction()
    yield True
    yield True


def downstream_transaction(context):
    context.open_transaction()
    return True


def test_transaction(rabbitmq):
    with AMQPComponent(downstream_transaction, subtopic="upstream_transaction_pub") as downstream_transaction_component:
        with AMQPComponent(upstream_transaction, pubtopic="upstream_transaction_pub") as upstream_transaction_component:
            upstream_transaction_component.send({})
            upstream_stack_1 = upstream_transaction_component.consume()["stack"]
            upstream_stack_2 = upstream_transaction_component.consume()["stack"]
            downstream_stack_1 = downstream_transaction_component.consume()["stack"]
            downstream_stack_2 = downstream_transaction_component.consume()["stack"]

            assert len(upstream_stack_1) == 1
            assert len(upstream_stack_2) == 1
            assert len(downstream_stack_1) == 2
            assert len(downstream_stack_2) == 2
            assert upstream_stack_1 == upstream_stack_2
            assert downstream_stack_1[0] == upstream_stack_1[0]
            assert downstream_stack_2[0] == upstream_stack_1[0]
            assert downstream_stack_1[1] != downstream_stack_2[1]


def nested_upstream_transaction(context):
    context.open_transaction()
    yield
    context.open_transaction()
    yield


def test_nested_transaction(rabbitmq):
    with AMQPComponent(downstream_transaction, subtopic="upstream_transaction_pub") as downstream_transaction_component:
        with AMQPComponent(nested_upstream_transaction, pubtopic="upstream_transaction_pub") as upstream_transaction_component:
            upstream_transaction_component.send({})
            upstream_stack_1 = upstream_transaction_component.consume()["metadata"]["stack"]
            upstream_stack_2 = upstream_transaction_component.consume()["metadata"]["stack"]
            downstream_stack_1 = downstream_transaction_component.consume()["metadata"]["stack"]
            downstream_stack_2 = downstream_transaction_component.consume()["metadata"]["stack"]

            assert len(upstream_stack_1) == 1
            assert len(upstream_stack_2) == 1
            assert len(downstream_stack_1) == 2
            assert len(downstream_stack_2) == 2
            assert upstream_stack_1 == upstream_stack_2
            assert downstream_stack_1[0] == upstream_stack_1[0]
            assert downstream_stack_2[0] == upstream_stack_1[0]
            assert downstream_stack_1[1] != downstream_stack_2[1]
