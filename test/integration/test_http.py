import unittest
import json
import requests
import datetime
import pytz
import decimal
import multiprocessing
from typing import Callable
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from src.ergo_cli import ErgoCli


class HTTPTest(unittest.TestCase):
    target_func: Callable

    def setUp(self) -> None:
        entrypoint = __file__ + ":" + self.target_func.__name__
        self._ergo_process = multiprocessing.Process(target=ErgoCli().http, args=(entrypoint,))
        self._ergo_process.start()

        # HTTP requests need to retry on ConnectionError while the Flask server boots.
        self.session = requests.Session()
        retries = Retry(connect=10, backoff_factor=0.1)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def tearDown(self) -> None:
        self._ergo_process.terminate()


def product(x, y):
    return float(x) * float(y)


class TestProduct(HTTPTest):
    target_func = product

    def test(self):
        """tests the example function from the ergo README"""
        resp = self.session.get("http://localhost?4&5")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body[0]["data"], 20)

    def test_named_params(self):
        resp = self.session.get("http://localhost", params={"x": 2.5, "y": 3})
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["data"] == 7.5

    def test_data_param(self):
        resp = self.session.get("http://localhost", params={"data": {"x": 2.5, "y": 3}})
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["data"] == 7.5


def product_alt(payload):
    return product(**json.loads(payload))


class TestProductAlt(HTTPTest):
    target_func = product_alt

    def test_payload(self):
        payload = json.dumps({"x": 2.5, "y": 3})
        resp = self.session.get("http://localhost", params={"data": payload})
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["data"] == 7.5


def get_data():
    return {
        "date": datetime.date(2021, 9, 15),
        "time": datetime.datetime(2021, 9, 15, 3, 30, tzinfo=pytz.timezone("America/New_York")),
        "number": decimal.Decimal(0.01234567890123456789)
    }


class TestGetData(HTTPTest):
    target_func = get_data

    def test(self):
        """asserts that the FlaskHttpInvoker can correctly serialize output with common standard library data types"""
        resp = self.session.get("http://localhost")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        actual = body[0]["data"]
        expected = {
            'date': '2021-09-15',
            'time': '2021-09-15T03:30:00-04:56',
            'number': '0.0123456789012345684308780136007044347934424877166748046875'
        }
        self.assertEqual(actual, expected)
