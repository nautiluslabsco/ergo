from src.http_invoker import HttpInvoker
from falcon import Request, Response  # type: ignore
from typing import Any

class FalconHttpInvoker(HttpInvoker):  # type: ignore
    def __init__(self, invocable: Any):
        HttpInvoker.__init__(self, invocable)

        self.add_route(self.route, self)

    def on_get(self, request: Request, response: Response) -> None:
        data_out: List[Any] = []
        data_in: List[Any] = request.params
        # data_in(f'route: {str(request.url_rule)}')
        try:
            self._invocable.invoke(data_in, data_out)
        except Exception as err:
            abort(400)

        response.body = str(data_out)
