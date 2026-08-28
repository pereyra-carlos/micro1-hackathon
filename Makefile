# incident-copilot — agentic root-cause diagnosis measured against a baseline.

.DEFAULT_GOAL := help

SHELL := /bin/bash

COMPOSE := docker compose -f lab/docker-compose.yml
VENV := .venv
PY := $(VENV)/bin/python
CASE ?=
N ?= 3

.PHONY: help setup test up down reset break smoke run eval validate clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtualenv and install host-side dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet -r requirements.txt

test: ## Run the test suite (no API key or running lab required)
	$(PY) -m pytest -q

up: ## Build and start the synthetic lab, wait until healthy
	$(COMPOSE) up -d --build --wait

down: ## Tear the lab down, removing volumes
	$(COMPOSE) down -v --remove-orphans

reset: down up ## Recreate the lab from scratch (deterministic clean state)

break: ## Inject a fault: make break CASE=<id>
	@test -n "$(CASE)" || (echo "usage: make break CASE=<id>" && exit 1)
	$(PY) scripts/break.py $(CASE)

smoke: ## Verify the healthy lab end to end
	./scripts/smoke.sh

run: ## Diagnose the current lab state with the agent: make run CASE=<id>
	@test -n "$(CASE)" || (echo "usage: make run CASE=<id>" && exit 1)
	$(PY) -m agent.run $(CASE)

eval: ## Full evaluation: N repetitions of every case, baseline vs agent
	$(PY) -m eval.run --repetitions $(N)

validate: ## Prove a fresh clone works: setup+test+up+smoke+down in a temp dir
	./scripts/validate.sh

clean: down ## Tear down the lab and remove local artifacts
	rm -rf $(VENV) .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
