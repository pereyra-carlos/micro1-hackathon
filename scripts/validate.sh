#!/usr/bin/env bash
# Validate reproducibility from a clean state: pipe the committed tree
# (git archive HEAD) into an ephemeral container and run the full
# setup/test/run cycle there. Uncommitted changes are deliberately
# excluded — this proves what a judge cloning the repo would get.
set -euo pipefail

IMAGE="${SANDBOX_IMAGE:-micro1-sandbox}"

cd "$(git rev-parse --show-toplevel)"

git archive HEAD | docker run --rm -i "$IMAGE" bash -euo pipefail -c '
    workdir="$(mktemp -d)"
    tar -xf - -C "$workdir"
    cd "$workdir"
    make setup
    make test
    make run
'

echo "validate: OK (setup, test, run passed in a clean container)"
