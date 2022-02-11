from test.integration.utils import Component
from test.integration.amqp.utils import AMQP_HOST, EXCHANGE


class GatewayComponent(Component):
    _ergo_command = "gateway"

    @property
    def namespace(self):
        ns = {
            "host": AMQP_HOST,
            "exchange": EXCHANGE,
        }
        return ns
