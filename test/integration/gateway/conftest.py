import pytest


@pytest.fixture(scope="session", autouse=True)
def auto_amqp_broker(amqp_broker):
    pass
