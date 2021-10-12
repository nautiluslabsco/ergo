import inspect

import pytest
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from test.integration.utils import ergo


# HTTP requests need to retry on ConnectionError while the Flask server boots.
session = requests.Session()
retries = Retry(connect=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))


def product(x, y):
    return float(x) * float(y)


def test_product():
    """tests the example function from the ergo README"""
    with ergo("http", f"{__file__}:product"):
        resp = session.get("http://localhost?x=4&y=5")
        assert resp.status_code == 200
        result = resp.json()
        assert result == 20.0


def test_product__post_request():
    with ergo("http", f"{__file__}:product"):
        resp = session.post("http://localhost?x=4&y=5")
        assert resp.status_code == 200
        result = resp.json()
        assert result == 20.0


def test_product__ergo_start():
    manifest = {
        "func": f"{__file__}:product"
    }
    namespace = {
        "protocol": "http",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        resp = session.get("http://localhost", params={"x": 2.5, "y": 3})
        assert resp.status_code == 200
        result = resp.json()
        assert result == 7.5


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


@pytest.mark.parametrize("getter", [
    get_dict,
    get_one_dict,
    get_two_dicts,
    get_none,
    yield_one_dict,
    yield_two_dicts,
])
def test_get_data(getter):
    """assert that ergo flask response data preserves the type and dimensionality of the component function's return
    value"""
    manifest = {
        "func": f"{__file__}:{getter.__name__}"
    }
    namespace = {
        "protocol": "http",
    }
    with ergo("start", manifest=manifest, namespace=namespace):
        resp = session.get("http://localhost")
        assert resp.ok
        actual = resp.json()
        if inspect.isgeneratorfunction(getter):
            expected = [i for i in getter()]
        else:
            expected = getter()

        assert actual == expected
