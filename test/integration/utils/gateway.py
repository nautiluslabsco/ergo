from test.integration.utils.amqp import AMQP_HOST, EXCHANGE
from test.integration.utils import Component


class HttpGateway(Component):
    _ergo_command = "gateway"

    @property
    def namespace(self):
        return {
            "host": AMQP_HOST,
            "exchange": EXCHANGE,
        }


http_gateway = HttpGateway
