from test.integration.utils import FunctionComponent


class HTTPComponent(FunctionComponent):
    @property
    def namespace(self):
        return {
            "protocol": "http",
        }
