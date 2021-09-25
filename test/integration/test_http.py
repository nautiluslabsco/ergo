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
    assert result == [20.0]


@with_ergo("start", "test/integration/configs/product.yml", "test/integration/configs/http.yml")
def test_product__ergo_start():
    resp = session.get("http://localhost", params={"x": 2.5, "y": 3})
    assert resp.status_code == 200
    result = resp.json()
    assert result == [7.5]


def get_data():
    return {
        "string": "🌟",
        "date": datetime.date(2021, 9, 15),
        "time": datetime.datetime(2021, 9, 15, 3, 30, tzinfo=pytz.timezone("America/New_York")),
        "decimal": decimal.Decimal("0.01234567890123456789"),
        "float": 0.01234567890123456789,
    }


@with_ergo("http", f"{__file__}:get_data")
def test_get_data():
    """asserts that the FlaskHttpInvoker can correctly serialize output with common standard library data types"""
    resp = session.get("http://localhost")
    assert resp.status_code == 200
    actual, = resp.json()
    expected = {
        "string": "🌟",
        'date': '2021-09-15',
        'time': '2021-09-15T03:30:00-04:56',
        'decimal': '0.01234567890123456789',
        'float': 0.012345678901234568,
    }
    assert actual == expected
