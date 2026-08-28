# Disposable sandbox for reproducibility validation.
# Only tooling needed to unpack the repo and drive the Makefile lives here;
# the challenge stack gets added once the statement drops.
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
