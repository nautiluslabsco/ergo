from test.integration.utils import FunctionComponent


class HttpComponent(FunctionComponent):
    @property
    def namespace(self):
        return {
            "protocol": "http",
        }
