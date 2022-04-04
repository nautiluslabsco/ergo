from test.integration.utils.amqp import ComponentFailure, amqp_component, propagate_errors, publish

import pytest

from ergo.context import Context


# @pytest.fixture(scope="session")
# def teardown_module():
#     yield
#     import time
#     while True:
#         print("sleeping")
#         time.sleep(1000)



"""
test_product
"""


def product(x, y):
    return float(x) * float(y)


def test_product_amqp(propagate_amqp_errors):
    with amqp_component(product, subtopic="my_topic") as component:
        component.send(x=4, y=5)
        assert component.consume(inactivity_timeout=None)["data"] == 20.0


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
        result = component.rpc(x=4)
    assert result["data"] == 8.0


"""
test_return_two_dicts
"""


def return_dict():
    return {"key": "value"}


def return_two_dicts():
    return [return_dict(), return_dict()]


def test_return_two_dicts():
    with amqp_component(return_two_dicts) as component:
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


def test_error_path():
    component = amqp_component(assert_false)
    with propagate_errors(), component:
        with pytest.raises(ComponentFailure):
            component.rpc(inactivity_timeout=None)


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


def test_make_six(propagate_amqp_errors):
    make_six_component = amqp_component(make_six, subtopic="make_six")
    forward_component = amqp_component(forward, subtopic="forward")
    double_component = amqp_component(double, subtopic="double_in", pubtopic="double_out")

    with make_six_component, forward_component, double_component:
        make_six_component.send()
        assert double_component.consume()["data"] == 6
