import multiprocessing
import subprocess
import requests
import unittest
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from src.ergo_cli import ErgoCli


class ErgoStartTest(unittest.TestCase):
    manifest: str
    namespace: str

    def setUp(self) -> None:
        self._ergo_process = multiprocessing.Process(target=ErgoCli().start, args=(self.manifest, self.namespace,))
        self._ergo_process.start()
        # self._ergo_process = subprocess.Popen(["ergo", "start", self.manifest, self.namespace])

        # HTTP requests need to retry on ConnectionError while the Flask server boots.
        self.session = requests.Session()
        retries = Retry(connect=5, backoff_factor=0.1)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def tearDown(self) -> None:
        self._ergo_process.terminate()
