from test.integration.amqp.utils import ComponentFailure, amqp_component
import pytest
from ergo.context import Context


def product(x, y=1):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    with amqp_component(product) as component:
        result = next(component.rpc({"x": 4, "y": 5}))
        assert result["data"] == 20.0


class Product:
    @classmethod
    def __call__(cls, x, y):
        return x * y


def test_product_class(rabbitmq):
    with amqp_component(Product) as component:
        result = next(component.rpc({"x": 4, "y": 5}))
        assert result["data"] == 20.0


def get_dict():
    return {"key": "value"}


def get_two_dicts():
    return [get_dict(), get_dict()]


def test_get_two_dicts(rabbitmq):
    with amqp_component(get_two_dicts) as component:
        result = next(component.rpc({}))
        assert result["data"] == get_two_dicts()


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


def test_yield_two_dicts(rabbitmq):
    with amqp_component(yield_two_dicts) as component:
        results = component.rpc({})
        assert next(results)["data"] == get_dict()
        assert next(results)["data"] == get_dict()


def assert_false():
    assert False


def test_error_path(rabbitmq):
    with amqp_component(assert_false) as component:
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
    with amqp_component(make_six, subtopic="make_six") as make_six_component:
        with amqp_component(forward, subtopic="forward") as forward_component:
            with amqp_component(double, subtopic="double_in", pubtopic="double_out") as double_component:
                double_sub = double_component.new_subscription(inactivity_timeout=0.1)
                make_six_component.send({})
                for attempt in range(20):
                    result = next(double_sub)
                    if result:
                        break
                    make_six_component.propagate_error(inactivity_timeout=0.1)
                    forward_component.propagate_error(inactivity_timeout=0.1)
                assert result["data"] == 6


def outer_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None
    return True


def intermediate_temporary_transaction(context):
    context.open_transaction()
    context.close_transaction()
    assert context._transaction is None
    return True


def inner_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None
    return True


def test_transaction(rabbitmq):
    with amqp_component(outer_transaction) as outer_transaction_component:
        with amqp_component(intermediate_temporary_transaction, subtopic=outer_transaction_component.pubtopic) as intermediate_component:
            with amqp_component(inner_transaction, subtopic=intermediate_component.pubtopic) as inner_transaction_component:
                outer_sub = outer_transaction_component.new_subscription(inactivity_timeout=0.1)
                inner_sub = inner_transaction_component.new_subscription(inactivity_timeout=0.1)
                outer_transaction_component.send({})
                outer_txn_result = inner_txn_result = None
                for attempt in range(20):
                    outer_txn_result = outer_txn_result or next(outer_sub)
                    inner_txn_result = inner_txn_result or next(inner_sub)
                    if outer_txn_result and inner_txn_result:
                        break
                    outer_transaction_component.propagate_error(0.1)
                    intermediate_component.propagate_error(0.1)
                    inner_transaction_component.propagate_error(0.1)
                outer_txn_stack = outer_txn_result["metadata"]["transaction_stack"]
                assert len(outer_txn_stack) == 1
                inner_txn_stack = inner_txn_result["metadata"]["transaction_stack"]
                assert len(inner_txn_stack) == 2
                assert inner_txn_stack[0] == outer_txn_stack[0]
