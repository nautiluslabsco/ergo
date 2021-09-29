import requests
import datetime
import pytz
import decimal
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from test.integration.utils import with_ergo


# HTTP requests need to retry on ConnectionError while the Flask server boots.
session = requests.Session()
retries = Retry(connect=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))


def product(x, y):
    return float(x) * float(y)


@with_ergo("http", f"{__file__}:product")
def test_product():
    """tests the example function from the ergo README"""
    resp = session.get("http://localhost?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result == 20.0


@with_ergo("start", "test/integration/configs/product.yml", "test/integration/configs/http.yml")
def test_product__ergo_start():
    resp = session.get("http://localhost", params={"x": 2.5, "y": 3})
    assert resp.status_code == 200
    result = resp.json()
    assert result == 7.5
