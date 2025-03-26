.PHONY: install-venv install-pw start docker vnc

export PYTHONPATH := src

ifneq (,$(wildcard .env))
    include .env
    export $(shell set -a && source .env && env | cut -d= -f1)
endif

install-venv:
	poetry config virtualenvs.in-project true
	poetry install

install-pw:
	playwright install

start:
	poetry run python ./src/main.py

docker:
	docker compose up

vnc:
	docker compose up -f ./ubuntu-vnc/docker-compose.yml