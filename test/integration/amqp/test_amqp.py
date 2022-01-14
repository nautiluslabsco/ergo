from test.integration.amqp.utils import ComponentFailure, AMQPComponent
import pytest
from ergo.context import Context
from typing import List


def product(x, y=1):
    return float(x) * float(y)


def test_product_amqp(rabbitmq):
    with AMQPComponent(product) as component:
        result = next(component.rpc({"x": 4, "y": 5}, inactivity_timeout=1))
        assert result["data"] == 20.0


class Product:
    @classmethod
    def __call__(cls, x, y):
        return x * y


def test_product_class(rabbitmq):
    with AMQPComponent(Product) as component:
        result = next(component.rpc({"x": 4, "y": 5}))
        assert result["data"] == 20.0


def get_dict():
    return {"key": "value"}


def get_two_dicts():
    return [get_dict(), get_dict()]


def test_get_two_dicts(rabbitmq):
    with AMQPComponent(get_two_dicts) as component:
        result = next(component.rpc({}))
        assert result["data"] == get_two_dicts()


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


def test_yield_two_dicts(rabbitmq):
    with AMQPComponent(yield_two_dicts) as component:
        results = component.rpc({})
        assert next(results)["data"] == get_dict()
        assert next(results)["data"] == get_dict()


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
                double_sub = double_component.new_subscription(inactivity_timeout=0.1)
                make_six_component.send({})
                for attempt in range(20):
                    result = next(double_sub)
                    if result:
                        break
                    make_six_component.propagate_error(inactivity_timeout=0.1)
                    forward_component.propagate_error(inactivity_timeout=0.1)
                assert result["data"] == 6


def outer_transaction(context, pubtopic):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None
    return True


def intermediate_temporary_transaction(context):
    context.open_transaction()
    context.close_transaction()  # what else should this do?
    assert context._transaction is None
    return True


def inner_transaction(context):
    assert context._transaction is None
    context.open_transaction()
    assert context._transaction is not None
    return True


def test_transaction(rabbitmq):
    with AMQPComponent(outer_transaction) as outer_transaction_component:
        with AMQPComponent(intermediate_temporary_transaction, subtopic=outer_transaction_component.pubtopic) as intermediate_component:
            with AMQPComponent(inner_transaction, subtopic=intermediate_component.pubtopic) as inner_transaction_component:
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


def assemble_sandwich(ergo, order: List):
    sandwich = []
    futures = [ergo.future("procure_topping", topping=topping) for topping in order]
    for future in futures:
        topping = yield future
        sandwich.append(topping)
    bill_future = ergo.future(INTERNAL_BIILLING_TOPIC, order=order)
    yield {"sandwich": sandwich, "bill_future": bill_future}


def assemble_sandwich(context, order: List):
    sandwich = []
    for selection in order:
        context.request("procure_topping", topping=selection)
    continuation = context.new_continuation()
    sandwich.append(context.load("topping"))
    if sandwich != order:
        return continuation.invoke()
    else:
        return sandwich




def assemble_sandwich(context, order: List, topping):  # noqa
    my_order = context.load("order")
    if not my_order:
        context.store("order", order)
        return context.jump_to_top
    sandwich = context.load("sandwich", [])
    sandwich.append(topping)
    for topping in order:
        if topping not in sandwich:
            context.store("sandwich", sandwich)
            context.request("procure_topping", topping=topping)
            return context.jump_to_top

    return sandwich
