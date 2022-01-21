from test.integration.start_rabbitmq_broker import start_rabbitmq_broker

import pytest


@pytest.fixture(scope="session", autouse=True)
def rabbitmq():
    start_rabbitmq_broker()
