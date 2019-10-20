from flask import Flask, request  # , abort

from src.http_invoker import HttpInvoker
from src.payload import Payload


class FlaskHttpInvoker(HttpInvoker):
    def start(self) -> int:
        app = Flask(__name__)

        @app.route(self.route)
        def handler() -> str:
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
        return False


# from werkzeug.serving import make_server
# import threading
# from multiprocessing import Process
# class ServerThread(threading.Thread):

#     def __init__(self, app):
#         threading.Thread.__init__(self)
#         self.srv = make_server('127.0.0.1', 5000, app)
#         self.ctx = app.app_context()
#         self.ctx.push()

#     def run(self):
#         print('starting server')
#         self.srv.serve_forever()

#     def shutdown(self):
#         self.srv.shutdown()

# class FlaskHttpInvoker(HttpInvoker):
#   def start(self) -> int:
#     global server
#     app = Flask('myapp')
#     #...
#     server = ServerThread(app)
#     server.start()
#     print('server started')

#   def stop(self):
#       global server
#       server = Process(target='myapp')
#       server.terminate()
#       server.join()
