"""Summary."""
from typing import List
import inspect
import json
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

        @app.route(self.route, methods=["GET", "POST"])
        def handler() -> str:  # type: ignore
            """Summary.

            Returns:
                str: Description

            """
            data_in: TYPE_PAYLOAD = dict(request.args)
            data_out: List[TYPE_PAYLOAD] = list(self._invocable.invoke(data_in))
            if not inspect.isgeneratorfunction(self._invocable.func):
                data_out = data_out[0]
            return json.dumps(data_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0
