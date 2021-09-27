ARG ERGO_PYTHON_VERSION

FROM python:${ERGO_PYTHON_VERSION}-slim as ergo-python

RUN apt-get update && apt-get install -y make

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY dev-requirements.txt /tmp/dev-requirements.txt
RUN pip install -r /tmp/dev-requirements.txt && rm /tmp/dev-requirements.txt

WORKDIR /app

COPY . .
