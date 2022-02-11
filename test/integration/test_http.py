import inspect
from test.integration.utils.http import http_component

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# HTTP requests need to retry on ConnectionError while the Flask server boots.
session = requests.Session()
retries = Retry(connect=5, backoff_factor=0.1)
session.mount("http://", HTTPAdapter(max_retries=retries))


def product(x, y):
    return float(x) * float(y)


@http_component(product)
def test_product():
    """tests the example function from the ergo README"""
    resp = session.get("http://localhost?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0


@http_component(product)
def test_product__post_request():
    resp = session.post("http://localhost?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0


def get_dict():
    return {
        "string": "🌟",
        "float": 1.234,
    }


def get_one_dict():
    return [get_dict()]


def get_two_dicts():
    return [get_dict(), get_dict()]


def get_none():
    return None


def yield_one_dict():
    yield get_dict()


def yield_two_dicts():
    yield get_dict()
    yield get_dict()


@pytest.mark.parametrize(
    "getter",
    [
        get_dict,
        get_one_dict,
        get_two_dicts,
        get_none,
        yield_one_dict,
        yield_two_dicts,
    ],
)
def test_get_data(getter):
    """assert that ergo flask response data preserves the type and dimensionality of the component function's return
    value"""
    with http_component(getter):
        resp = session.get("http://localhost")
        assert resp.ok
        response = resp.json()
        if inspect.isgeneratorfunction(getter):
            expected = [i for i in getter()]
            actual = [d["data"] for d in response]
        else:
            expected = getter()
            actual = response["data"]

        assert actual == expected
