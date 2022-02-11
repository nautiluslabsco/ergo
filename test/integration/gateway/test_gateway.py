from test.integration.gateway.utils import GatewayComponent
from test.integration.utils.amqp import amqp_component


def foo():
    return "bar"


@GatewayComponent()
@amqp_component(foo, subtopic="foo")
def test_gateway():
    while True:
        pass
