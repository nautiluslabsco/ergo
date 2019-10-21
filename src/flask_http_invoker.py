"""Summary."""
from flask import Flask, request  # , abort

from src.http_invoker import HttpInvoker
from src.payload import Payload


class FlaskHttpInvoker(HttpInvoker):
    """Summary."""

    def start(self) -> int:
        """Summary.

        Returns:
            int: Description

        """
        app: Flask = Flask(__name__)

        @app.route(self.route)
        def handler() -> str:
            """Summary.

            Returns:
                str: Description

            """
            data_out: Payload = Payload()
            data_in: Payload = Payload(dict(request.args))
            # data_in(f'route: {str(request.url_rule)}')
            # try:
            self._invocable.invoke(data_out, data_in)
            # except Exception as err:
            #     print(err)
            #     abort(400)

            return str(data_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0
