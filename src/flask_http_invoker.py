"""Summary."""
from typing import List

from flask import Flask, request  # , abort

from src.http_invoker import HttpInvoker
from src.types import TYPE_PAYLOAD


class FlaskHttpInvoker(HttpInvoker):
    """Summary."""

    def start(self) -> int:
        """Summary.

        Returns:
            int: Description

        """
        app: Flask = Flask(__name__)

        @app.route(self.route)
        def handler() -> str:  # type: ignore
            """Summary.

            Returns:
                str: Description

            """
            data_out: List[TYPE_PAYLOAD] = []
            data_in: TYPE_PAYLOAD = dict(request.args)
            # data_in(f'route: {str(request.url_rule)}')
            # try:
            for result in self._invocable.invoke(data_in):
                data_out.append(result)
            # except Exception as err:
            #     print(err)
            #     abort(400)

            return str(data_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0
