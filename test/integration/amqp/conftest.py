from test.integration.start_rabbitmq_broker import start_rabbitmq_broker

import pytest


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()
