from test.integration.start_rabbitmq_broker import start_rabbitmq_broker

import pytest


@pytest.fixture(scope="session")
def amqp_broker():
    start_rabbitmq_broker()
