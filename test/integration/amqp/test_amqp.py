from test.integration.utils.amqp import ComponentFailure, amqp_component, publish, Queue

import pytest

from ergo.context import Context

"""
test_product
"""


def product(x, y):
    return float(x) * float(y)


@amqp_component(product)
def test_product_amqp(component):
    result = component.rpc(x=4, y=5)
    assert result["data"] == 20.0


"""
test_product_class
test_product_instance

Assert that ergo can inject class or instance methods, and non-null default args.

"""


class Product:
    @classmethod
    def __call__(cls, x, y=2):
        return x * y


product_instance = Product()


@amqp_component(Product)
def test_product_class(component):
    result = component.rpc(x=4)
    assert result["data"] == 8.0


@amqp_component(product_instance)
def test_product_instance(component):
    result = component.rpc(x=4, inactivity_timeout=None)
    assert result["data"] == 8.0


"""
test_return_two_dicts
"""


def return_dict():
    return {"key": "value"}


def return_two_dicts():
    return [return_dict(), return_dict()]


@amqp_component(return_two_dicts)
def test_return_two_dicts(component):
    result = component.rpc()
    assert result["data"] == return_two_dicts()


"""
test_yield_two_dicts
"""


def yield_two_dicts():
    yield return_dict()
    yield return_dict()


@amqp_component(yield_two_dicts)
def test_yield_two_dicts(component):
    component.send()
    assert component.consume()["data"] == return_dict()
    assert component.consume()["data"] == return_dict()


"""
test_error_path
"""


def assert_false():
    assert False


@amqp_component(assert_false)
def test_error_path(component):
    with pytest.raises(ComponentFailure):
        component.send()
        component.propagate_error()


"""
test_make_six

Assert that a component can forward messages dynamically by setting context.pubtopic.

"""


def make_six(context: Context):
    context.pubtopic = "forward"
    return {"recipient": "double_in", "x": 3}


def forward(context, data):
    context.pubtopic = data.pop("recipient")
    return data


def double(x: float):
    return 2 * x


@amqp_component(make_six, subtopic="make_six")
@amqp_component(forward, subtopic="forward")
@amqp_component(double, subtopic="double_in", pubtopic="double_out")
def test_make_six(components):
    make_six_component, forward_component, double_component = components
    make_six_component.send()
    result = double_component.consume()
    if not result:
        make_six_component.propagate_error(inactivity_timeout=0.1)
        forward_component.propagate_error(inactivity_timeout=0.1)
    assert result["data"] == 6


"""
test_bind_data_to_my_param
test_bind_data_index_foo_to_my_param
test_dont_bind_data

These tests assert that ergo can correctly bind message data to a custom parameter using the `args` configuration attribute.
"""


def handler_with_mapped_params(my_context: Context, my_param):
    assert my_context.pubtopic
    return my_param


@amqp_component(handler_with_mapped_params, args={"my_param": "data", "my_context": "context"})
def test_bind_data_to_my_param(component):
    results = Queue(routing_key=component.pubtopic)
    publish(component.subtopic, foo="bar")
    assert results.consume()["data"] == {"foo": "bar"}
    publish(component.subtopic, data={"foo": "bar"})
    assert results.consume()["data"] == {"foo": "bar"}
    publish(component.subtopic, something_else="bar")
    assert results.consume()["data"] == {"something_else": "bar"}


@amqp_component(handler_with_mapped_params, args={"my_param": "data.foo", "my_context": "context"})
def test_bind_data_index_foo_to_my_param(component):
    results = Queue(routing_key=component.pubtopic)
    errors = Queue(routing_key=component.error_queue_name)
    publish(component.subtopic, foo="bar")
    assert results.consume()["data"] == "bar"
    publish(component.subtopic, data={"foo": "bar"})
    assert results.consume()["data"] == "bar"
    publish(component.subtopic, something_else="bar")
    error_result = errors.consume()
    assert "missing 1 required positional argument: 'my_param'" in error_result["error"]["message"]


@amqp_component(handler_with_mapped_params, args={"my_context": "context"})
def test_dont_bind_data(component):
    results = Queue(routing_key=component.pubtopic)
    publish(component.subtopic, my_param="my argument")
    assert results.consume()["data"] == "my argument"
