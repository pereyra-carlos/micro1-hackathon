#!/usr/bin/env bash
# Validate reproducibility from a clean state: extract the committed tree
# (git archive HEAD) into a temp dir and run setup, the test suite, and the
# full lab lifecycle with the end-to-end smoke test there. Uncommitted
# changes are deliberately excluded -- this proves what a judge cloning the
# repo would get. Live eval runs are excluded: they need ANTHROPIC_API_KEY.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
workdir="$(mktemp -d)"

# A dedicated project name and port so validation never collides with a
# lab already running from the working tree.
export COMPOSE_PROJECT_NAME=incident-lab-validate
export LAB_HTTP_PORT="${VALIDATE_HTTP_PORT:-18081}"

cleanup() {
    (cd "$workdir" 2>/dev/null && make down >/dev/null 2>&1) || true
    rm -rf "$workdir"
}
trap cleanup EXIT

git archive HEAD | tar -x -C "$workdir"
cd "$workdir"

make setup
make test
make up
./scripts/smoke.sh
make down

echo "validate: OK (setup, test, up, smoke, down passed from a clean tree)"
