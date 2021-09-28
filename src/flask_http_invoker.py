"""Summary."""
from typing import List
import json
import datetime
import decimal
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
            for result in self._invocable.invoke(data_in):
                data_out.append(result)
            if len(data_out) == 1:
                data_out = data_out[0]
            return json.dumps(data_out, cls=ErgoEncoder)

        app.run(host='0.0.0.0', port=self._port)
        return 0


class ErgoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
