import pytest


@pytest.fixture(scope="session", autouse=True)
def autouse_amqp_broker(amqp_broker):
    pass
