"""Summary."""
import inspect
from typing import List

from flask import Flask, request  # , abort

from ergo.http_invoker import HttpInvoker
from ergo.message import Message, decode, encodes


class FlaskHttpInvoker(HttpInvoker):
    """Summary."""

    def start(self) -> int:
        """Summary.

        Returns:
            int: Description

        """
        app: Flask = Flask(__name__)

        @app.route(self.route, methods=['GET', 'POST'])
        def handler() -> str:  # type: ignore
            """Summary.

            Returns:
                str: Description

            """
            data_in: Message = decode(**request.args)
            data_out: List[Message] = list(self.invoke_handler(data_in))
            if not inspect.isgeneratorfunction(self._invocable.func):
                data_out = data_out[0]
            return encodes(data_out)

        app.run(host='0.0.0.0', port=self._port)
        return 0
