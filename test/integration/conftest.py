import logging
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from test.integration.utils.amqp import propagate_errors, EXCHANGE, CONNECTION
import kombu

import pytest
import requests
from requests.adapters import HTTPAdapter, Retry

logging.getLogger("pika").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def amqp_broker():
    start_rabbitmq_broker()


@pytest.fixture()
def propagate_amqp_errors():
    with propagate_errors():
        yield


@pytest.fixture()
def http_session():
    # requests need to retry on ConnectionError while our HTTP server boots.
    session = requests.Session()
    retries = Retry(total=None, connect=50, backoff_factor=0.00001)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    # these retries generate a ton of warnings
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
    return session
