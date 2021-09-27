.PHONY: help clean dev docs package test

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "	 dev 	install all deps for dev env"
	@echo "  docs	create pydocs for all relveant modules"
	@echo "  build	build a new ergo docker image for testing"
	@echo "	 test	run all tests with coverage"

clean:
	rm -rf dist/*

dev:
	pip install -r dev-requirements.txt
	pip install -e .

docs:
	$(MAKE) -C docs html

build:
	docker-compose build

test:
	docker-compose run ergo make docker_test

docker_test:
	coverage run -m unittest discover -v
	coverage html
