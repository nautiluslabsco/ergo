from test.integration.start_rabbitmq_broker import start_rabbitmq_broker

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@pytest.fixture(scope="session")
def amqp_broker():
    start_rabbitmq_broker()


@pytest.fixture(scope="function")
def http_session():
    # requests need to retry on ConnectionError while the HTTP server boots.
    session = requests.Session()
    retries = Retry(connect=5, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session
