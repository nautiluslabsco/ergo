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
