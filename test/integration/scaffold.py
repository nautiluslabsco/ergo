import multiprocessing
import requests
import unittest
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from src.ergo_cli import ErgoCli


class ErgoStartTest(unittest.TestCase):
    manifest: str
    namespace: str
    session: requests.Session
    _ergo_process: multiprocessing.Process

    @classmethod
    def setUpClass(cls) -> None:
        manifest = str(Path(Path(__file__).parent, cls.manifest).resolve())
        namespace = str(Path(Path(__file__).parent, cls.namespace).resolve())
        cls._ergo_process = multiprocessing.Process(target=ErgoCli().start, args=(manifest, namespace,))
        cls._ergo_process.start()

        # HTTP requests need to retry on ConnectionError while the Flask server boots.
        cls.session = requests.Session()
        retries = Retry(connect=5, backoff_factor=0.1)
        cls.session.mount('http://', HTTPAdapter(max_retries=retries))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._ergo_process.terminate()
