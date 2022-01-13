import docker
import pika
import pika.exceptions
from test.integration.utils import retries


AMQP_HOST = "amqp://guest:guest@localhost:5672/%2F"


def start_rabbitmq_broker():
    """
    Start a rabbitmq server if none is running, and then wait for the broker to finish booting.
    """
    docker_client = docker.from_env()
    if not docker_client.containers.list(filters={"name": "rabbitmq"}):
        docker_client.containers.run(
            name="rabbitmq",
            image="rabbitmq:3.8.16-management-alpine",
            ports={5672: 5672, 15672: 15672},
            detach=True,
        )

    print("awaiting broker")
    for retry in retries(200, 0.5, pika.exceptions.AMQPConnectionError):
        with retry():
            pika.BlockingConnection(pika.URLParameters(AMQP_HOST))
    print("broker started")


if __name__ == "__main__":
    start_rabbitmq_broker()
