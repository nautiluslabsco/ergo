from test.integration.utils.amqp import AMQP_HOST, EXCHANGE
from test.integration.utils import Component


class GatewayComponent(Component):
    _ergo_command = "gateway"

    @property
    def namespace(self):
        ns = {
            "host": AMQP_HOST,
            "exchange": EXCHANGE,
        }
        return ns
