.PHONY: install-venv install-pw start

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
