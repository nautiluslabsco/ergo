import pytest
from test.integration.start_rabbitmq_broker import start_rabbitmq_broker


@pytest.fixture(scope="session")
def rabbitmq():
    start_rabbitmq_broker()
