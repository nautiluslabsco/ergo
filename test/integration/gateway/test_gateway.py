from test.integration.utils.gateway import http_gateway
from test.integration.utils.amqp import amqp_component
from functools import partial
from multiprocessing.pool import ThreadPool


"""
test_double
"""


def product(x, y):
    return float(x) * float(y)


def double(sesh, x: int):
    resp = sesh.get("http://localhost/product", params={"x": x, "y": 2})
    return {x: resp.json()["data"]}


@http_gateway()
@amqp_component(product, subtopic="product")
def test_double(components, http_session):
    pool = ThreadPool(10)
    actual = pool.map(partial(double, http_session), range(20))
    expected = [
        {0: 0.0},
        {1: 2.0},
        {2: 4.0},
        {3: 6.0},
        {4: 8.0},
        {5: 10.0},
        {6: 12.0},
        {7: 14.0},
        {8: 16.0},
        {9: 18.0},
        {10: 20.0},
        {11: 22.0},
        {12: 24.0},
        {13: 26.0},
        {14: 28.0},
        {15: 30.0},
        {16: 32.0},
        {17: 34.0},
        {18: 36.0},
        {19: 38.0},
    ]
    assert actual == expected


"""
test_gateway_routing
"""


def bar():
    return "bar"


@http_gateway()
@amqp_component(bar, subtopic="bar")
def test_gateway_routing(components, http_session):
    response = http_session.get("http://localhost/foo/bar")
    assert response.json()["data"] == "bar"


"""
test_yield_twice

Assert that a gateway request fulfilled by a generator component returns the first item yielded.
"""


def yield_twice():
    yield 1
    yield 2


@http_gateway()
@amqp_component(yield_twice, subtopic="yield_twice")
def test_yield_twice(components, http_session):
    response = http_session.get("http://localhost/yield_twice")
    assert response.json()["data"] in [1, 2]
