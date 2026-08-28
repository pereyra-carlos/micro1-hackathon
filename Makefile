# micro1 Frontier Engineering Challenge 2026
#
# Placeholder targets. The real commands land once the challenge statement
# drops and the stack is chosen. Keep the target names stable so the README
# and CI never have to change.

.DEFAULT_GOAL := help

SHELL := /bin/bash

SANDBOX_IMAGE := micro1-sandbox

.PHONY: help setup test run up down clean validate

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies from a clean clone
	@echo "TODO: install dependencies (package manager / virtualenv / docker build)"

test: ## Run the full test suite
	@echo "TODO: run the test suite"

run: ## Run the application locally
	@echo "TODO: start the application"

up: ## Bring the whole stack up (docker compose)
	@echo "TODO: docker compose up --build"

down: ## Tear the stack down
	@echo "TODO: docker compose down -v"

validate: ## Run setup+test+run on HEAD inside a disposable container
	@docker image inspect $(SANDBOX_IMAGE) >/dev/null 2>&1 \
		|| docker build -f sandbox.Dockerfile -t $(SANDBOX_IMAGE) .
	@SANDBOX_IMAGE=$(SANDBOX_IMAGE) ./scripts/validate.sh

clean: ## Remove build artifacts and caches
	@echo "TODO: remove build artifacts and caches"
