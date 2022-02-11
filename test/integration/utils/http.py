from test.integration.utils import FunctionComponent


class HTTPComponent(FunctionComponent):
    protocol = "http"


http_component = HTTPComponent
