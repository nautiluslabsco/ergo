# pylint: disable-all
# flake8: noqa
# type: ignore
"""Summary."""

from typing import Any, List

from falcon import Request, Response, abort

from src.http_invoker import HttpInvoker


class FalconHttpInvoker(HttpInvoker):

    """Summary"""

    def __init__(self, invocable: Any):
        """Summary

        Args:
            invocable (Any): Description
        """
        super().__init__(self, invocable)

    def on_get(self, request: Request, response: Response) -> None:
        """Summary

        Args:
            request (Request): Description
            response (Response): Description
        """
        data_out: List[Any] = []
        data_in: List[Any] = request.params
        # data_in(f'route: {str(request.url_rule)}')
        try:
            self._invocable.invoke(data_in, data_out)
        except Exception as err:
            print(str(err))
            abort(400)

        response.body = str(data_out)
