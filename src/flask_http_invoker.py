from flask import Flask, request, abort
from src.http_invoker import HttpInvoker

class FlaskHttpInvoker(HttpInvoker):
    def start(self) -> int:
        app = Flask(__name__)

        @app.route(self.route)
        def handler() -> str:
            data_out: List[Any] = []
            data_in: List[Any] = request.args
            # data_in(f'route: {str(request.url_rule)}')
            try:
                self._invocable.invoke(data_in, data_out)
            except Exception as err:
                print(err)
                abort(400)

            return str(data_out)

        app.run()
        return 0
