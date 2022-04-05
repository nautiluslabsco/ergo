from test.integration.utils import Component
from test.integration.utils.amqp import AMQP_HOST, EXCHANGE


class HTTPGateway(Component):
    _ergo_command = "gateway"

    @property
    def namespace(self):
        return {
            "host": AMQP_HOST,
            "exchange": EXCHANGE,
        }
