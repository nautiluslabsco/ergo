from test.integration.utils import FunctionComponent, retries
import requests
from requests.adapters import HTTPAdapter
import threading


class HTTPComponent(FunctionComponent):
    @property
    def namespace(self):
        return {
            "protocol": "http",
        }


def http_session():
    session = requests.Session()
    session.mount("http://", HTTPAdapter(pool_maxsize=20))

    # block until our HTTP server boots
    done_event = threading.Event()
    continue_event = threading.Event()

    def get_health_endpoint():
        session.get("http://0.0.0.0/health")
        done_event.set()
        continue_event.set()

    while not done_event.is_set():
        threading.Timer(0.1, continue_event.set).start()
        threading.Thread(target=get_health_endpoint).start()
        continue_event.wait()
    return session
