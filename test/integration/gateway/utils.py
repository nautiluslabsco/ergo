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

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._instance.process.kill()
        super().__exit__(exc_type, exc_val, exc_tb)


gateway_component = GatewayComponent
