import multiprocessing
import tempfile
import contextlib
import yaml
import json
import pika
import time
from contextlib import contextmanager, asynccontextmanager
from typing import Dict
from src.ergo_cli import ErgoCli


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


class Config:
    def __init__(self, manifest=None, namespace=None, func=None, protocol=None, exchange=None, pubtopic=None,
                 subtopic=None):
        self._manifest = manifest
        if manifest:
            with open(manifest, "r") as fh:
                manifest_data = yaml.safe_load(fh)
        else:
            manifest_data = {}
        self._namespace = namespace
        if namespace:
            with open(namespace, "r") as fh:
                namespace_data = yaml.safe_load(fh)
        else:
            namespace_data = {}
        self.func = func or manifest_data.get("func")
        self.protocol = protocol or manifest_data.get("protocol") or namespace_data.get("protocol")
        self.exchange = exchange or manifest_data.get("exchange") or namespace_data.get("exchange")
        self.pubtopic = pubtopic or manifest_data.get("pubtopic") or namespace_data.get("pubtopic")
        self.subtopic = subtopic or manifest_data.get("subtopic") or namespace_data.get("subtopic")

    @contextmanager
    def manifest(self):
        if self._manifest:
            yield self._manifest
        else:
            with tempfile.NamedTemporaryFile(mode="w+") as manifest:
                manifest.write(yaml.dump({"func": self.func, "protocol": self.protocol}))
                manifest.seek(0)
                yield manifest.name

    @contextmanager
    def namespace(self):
        if self._namespace:
            yield self._namespace
        else:
            with tempfile.NamedTemporaryFile(mode="w+") as namespace:
                namespace.write(
                    yaml.dump({"exchange": self.exchange, "pubtopic": self.pubtopic, "subtopic": self.subtopic}))
                namespace.seek(0)
                yield namespace.name


@asynccontextmanager
# def ergo_start(manifest=None, namespace=None, func=None, protocol=None, exchange=None, pubtopic=None, subtopic=None):
async def run(config):
    """
    This context manager starts a temporary ergo worker in a subprocess. The worker is terminated at __exit__ time.
    """
    # with _prepare_inputs(manifest=manifest, namespace=namespace, func=func, protocol=protocol, exchange=exchange,
    #                      pubtopic=pubtopic, subtopic=subtopic) as (manifest, namespace,):
    with config.manifest() as manifest:
        with config.namespace() as namespace:
            process = multiprocessing.Process(
                target=ErgoCli().start,
                args=(manifest, namespace),
            )
            process.start()
            try:
                yield process
            finally:
                process.terminate()


@contextmanager
def _prepare_inputs(manifest=None, namespace=None, func=None, protocol=None, exchange=None, pubtopic=None, subtopic=None):
    manifest_file = namespace_file = None
    if not manifest:
        manifest_file = tempfile.NamedTemporaryFile(mode="w+")
        manifest_file.write(yaml.dump({"func": func, "protocol": protocol}))
        manifest_file.seek(0)
        manifest = manifest_file.name
    if not namespace:
        namespace_file = tempfile.NamedTemporaryFile(mode="w+")
        namespace_file.write(yaml.dump({"exchange": exchange, "pubtopic": pubtopic, "subtopic": subtopic}))
        namespace_file.seek(0)
        namespace = namespace_file.name
    try:
        yield manifest, namespace
    finally:
        if manifest_file:
            manifest_file.close()
        if namespace_file:
            namespace_file.close()


def rpc(payload, config: Config):
    ret = {}

    connection = pika.BlockingConnection(pika.URLParameters(AMQP_HOST))
    channel = connection.channel()
    for retry in _retries(20, 0.5, pika.exceptions.ChannelClosedByBroker):
        with retry():
            channel.exchange_declare(config.exchange, passive=True)

    def on_pubtopic_message(body):
        result = body["data"]
        ret["result"] = result

    def on_error_mesage(body):
        error = body["error"]
        ret["error"] = error

    def add_consumer(queue_name, consumer):
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=config.exchange, queue=queue_name)
        channel.queue_purge(queue_name)

        def on_message_callback(chan, method, properties, body):
            channel.stop_consuming()
            body = json.loads(body)
            return consumer(body)

        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)

    add_consumer(config.pubtopic, on_pubtopic_message)
    add_consumer(f"{config.func}_error", on_error_mesage)

    # The ergo consumer may still be booting, so we have to retry publishing the message until it lands outside
    # of the dead letter queue.
    channel.confirm_delivery()
    for retry in _retries(10, 0.5, pika.exceptions.UnroutableError):
        with retry():
            channel.basic_publish(exchange=config.exchange, routing_key=config.subtopic,
                                  body=payload, mandatory=True)  # noqa

    try:
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()

    if ret.get("error"):
        raise Exception(ret["error"])
    return ret["result"]


def load_configs(*configs: str) -> Dict:
    merged = {}
    for config_file in configs:
        with open(config_file, "r") as fh:
            config = yaml.safe_load(fh)
            merged.update(config)
    return merged


def _retries(n: int, backoff_seconds: float, *retry_errors: BaseException):
    retry_errors = retry_errors or (Exception,)
    success = set()

    for attempt in range(n):
        @contextlib.contextmanager
        def retry():
            try:
                yield
                success.add(True)
            except retry_errors:
                if attempt+1 == n:
                    raise
                time.sleep(backoff_seconds)

        if not success:
            yield retry
