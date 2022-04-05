from test.integration.utils.amqp import AMQPComponent, ComponentFailure

import pytest

from ergo.context import Context

"""
test_product
"""


def product(x, y):
    return float(x) * float(y)


def test_product_amqp():
    with AMQPComponent(product) as component:
        component.send({"x": 4, "y": 5})
        assert component.consume(timeout=None).data == 20.0


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


def test_product_class():
    with AMQPComponent(Product) as component:
        result = component.rpc({"x": 4})
    assert result.data == 8.0


def test_product_instance():
    with AMQPComponent(product_instance) as component:
        result = component.rpc({"x": 4})
    assert result.data == 8.0


"""
test_return_two_dicts
"""


def return_dict():
    return {"key": "value"}


def return_two_dicts():
    return [return_dict(), return_dict()]


def test_return_two_dicts():
    with AMQPComponent(return_two_dicts) as component:
        result = component.rpc({})
    assert result.data == return_two_dicts()


"""
test_yield_two_dicts
"""


def yield_two_dicts():
    yield return_dict()
    yield return_dict()


def test_yield_two_dicts():
    with AMQPComponent(yield_two_dicts) as component:
        component.send({})
        assert component.consume().data == return_dict()
        assert component.consume().data == return_dict()


"""
test_error_path
"""


def assert_false():
    assert False


def test_error_path():
    component = AMQPComponent(assert_false)
    with component:
        with pytest.raises(ComponentFailure):
            component.rpc({})


"""
test_make_six

Assert that a component can forward messages dynamically by setting context.pubtopic.

"""


def make_six(context: Context):
    context.pubtopic = "forward"
    return {"recipient": "double_in", "x": 3}


def forward(context: Context, data):
    context.pubtopic = data.pop("recipient")
    return data


def double(x: float):
    return 2 * x


def test_make_six():
    make_six_component = AMQPComponent(make_six)
    forward_component = AMQPComponent(forward, subtopic="forward")
    double_component = AMQPComponent(double, subtopic="double_in")

    with make_six_component, forward_component, double_component:
        make_six_component.send({})
        assert double_component.consume().data == 6
