from test.integration.start_rabbitmq_broker import start_rabbitmq_broker
from test.integration.utils import retries

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@pytest.fixture(scope="session")
def amqp_broker():
    start_rabbitmq_broker()
