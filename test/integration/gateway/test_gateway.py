from test.integration.gateway.utils import gateway_component
from test.integration.utils.amqp import amqp_component
from test.integration.utils.http import http_session


def product(x, y):
    return float(x) * float(y)


@gateway_component()
@amqp_component(product, subtopic="product")
def test_gateway(components):
    sesh = http_session()
    resp = sesh.get("http://0.0.0.0/product?x=4&y=5")
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"] == 20.0
