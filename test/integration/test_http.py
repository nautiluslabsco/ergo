import inspect
from test.integration.utils.http import http_component

import pytest


def product(x, y):
    return float(x) * float(y)


@http_component(product)
def test_product(http_session):
    """tests the example function from the ergo README"""
    resp = http_session.get("http://localhost?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0


@http_component(product)
def test_product__post_request(http_session):
    resp = http_session.post("http://localhost?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0


def return_dict():
    return {
        "string": "🌟",
        "float": 1.234,
    }


def return_one_dict():
    return [return_dict()]


def return_two_dicts():
    return [return_dict(), return_dict()]


def return_none():
    return None


def yield_one_dict():
    yield return_dict()


def yield_two_dicts():
    yield return_dict()
    yield return_dict()


@pytest.mark.parametrize("getter", [
    return_dict,
    return_one_dict,
    return_two_dicts,
    return_none,
    yield_one_dict,
    yield_two_dicts,
])
def test_return_data(getter, http_session):
    """assert that ergo flask response data preserves the type and dimensionality of the component function's return
    value"""
    with http_component(getter):
        resp = http_session.get("http://localhost")
        assert resp.ok
        response = resp.json()
        if inspect.isgeneratorfunction(getter):
            expected = [i for i in getter()]
            actual = [d["data"] for d in response]
        else:
            expected = getter()
            actual = response["data"]

        assert actual == expected
