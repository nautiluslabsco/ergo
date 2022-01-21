from test.integration.amqp.utils import amqp_component, ComponentFailure

import pytest

from ergo.context import Context


"""
test_product
"""


def product(x, y):
    return float(x) * float(y)


def test_product_amqp():
    with amqp_component(product) as component:
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


def test_product_class():
    with amqp_component(Product) as component:
        result = component.rpc(x=4)
        assert result["data"] == 8.0


def test_product_instance():
    with amqp_component(product_instance) as component:
        result = component.rpc(x=4, inactivity_timeout=None)
        assert result["data"] == 8.0


"""
test_get_two_dicts
"""


def get_dict():
    return {"key": "value"}


def get_two_dicts():
    return [get_dict(), get_dict()]


def test_get_two_dicts():
    with amqp_component(get_two_dicts) as component:
        result = component.rpc()
        assert result["data"] == get_two_dicts()


"""
test_yield_two_dicts
"""


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


def test_yield_two_dicts():
    with amqp_component(yield_two_dicts) as component:
        component.send()
        assert component.consume()["data"] == get_dict()
        assert component.consume()["data"] == get_dict()


"""
test_error_path
"""


def assert_false():
    assert False


def test_error_path():
    with amqp_component(assert_false) as component:
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
