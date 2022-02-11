from test.integration.gateway.utils import GatewayComponent
from test.integration.utils.amqp import amqp_component


def product(x, y):
    return float(x) * float(y)


@GatewayComponent()
@amqp_component(product, subtopic="product")
def test_gateway(components, http_session):
    resp = http_session.get("http://0.0.0.0/product?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0
