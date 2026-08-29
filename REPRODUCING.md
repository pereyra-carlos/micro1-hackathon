# Reproducing the results

Written for a clean environment. Everything below was exercised end to end on
Linux with Docker 29.1 / Compose v5.1 and Python 3.10; `make validate` re-runs
the core of it from a pristine copy of the committed tree on every invocation.

## Prerequisites

- Docker with the compose plugin (tested: Docker 29.1.3, Compose v5.1.2).
- Python 3.10+ and GNU make.
- ~2 GB free disk for images (postgres:16-alpine, redis:7-alpine,
  nginx:1.27-alpine, curlimages/curl:8.10.1, python:3.12-slim base).
- An Anthropic API key — needed **only** for baseline/agent/eval runs; the
  lab, tests, and `make validate` work without it.

## Setup

```bash
git clone https://github.com/pereyra-carlos/micro1-hackathon.git
cd micro1-hackathon
make setup                          # venv + pinned host-side deps
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env   # gitignored; or export it
```

Versions are pinned: host deps in `requirements.txt` (anthropic 1.2.0,
PyYAML 6.0.3, pytest 9.1.1), service deps in `lab/app/requirements.txt`,
images by tag in `lab/docker-compose.yml`. The model comes from
`ANTHROPIC_MODEL` (default `claude-sonnet-5`); all recorded results used
that default. Current Claude models reject sampling parameters, so there is
no temperature setting — variance is handled by N=3 repetitions.

## The lab

```bash
make up             # build + start, waits for health checks (~1-2 min first time)
make smoke          # end-to-end canary; expected last line:
                    #   smoke: OK (api, db, queue, worker all healthy)
make break CASE=redis-oom    # inject a fault (see cases/cases.yaml for ids)
make reset          # deterministic clean state (down -v && up)
make down           # tear down
```

If host port 18080 is taken, prefix commands with `LAB_HTTP_PORT=<port>`.

## Single diagnosis runs (needs the API key)

```bash
make break CASE=api-dns && sleep 25
.venv/bin/python -m baseline.run api-dns    # one-call baseline, prints JSON
make run CASE=api-dns                       # agent; also writes
                                            # trajectories/api-dns/<run-id>.jsonl
make render                                 # readable .md next to every .jsonl
```

Both print a JSON object whose `answer` holds the structured diagnosis
(`root_cause_component`, `root_cause_type`, `explanation`, `evidence`,
`suggested_fix`) plus token usage and wall time.

## Full evaluation

```bash
make eval                                        # 6 cases x N=3 x both systems
.venv/bin/python -m eval.run --systems agent     # agent only (frozen baseline)
.venv/bin/python -m eval.run --case redis-oom --repetitions 1   # one slice
```

The runner resets the lab and re-injects the fault before every repetition,
streams graded rows to `results/<utc-stamp>/results.json` after each run
(interruption-safe), and writes `summary.md` at the end. Grading compares the
structured enums against `cases/cases.yaml` ground truth: component must
match exactly; fault_type must be in the case's `accepted_fault_types`.

### Measured runtime and cost (from the committed results)

Token prices: claude-sonnet-5 at $2/M input, $10/M output (Aug 2026).

| Sweep | Rows | Tokens (in / out) | API cost | Wall clock |
| --- | --- | --- | --- | --- |
| Both systems, 6 cases, N=3 (`results/20260828-205644`) | 36 | 1.64M / 131k | ~$4.60 | ~48 min |
| Agent only, 6 cases, N=3 (`results/20260829-025117`) | 18 | 0.95M / 66k | ~$2.56 | ~36 min |
| Agent only, 10 cases, N=3, prompt caching (`results/20260829-144721`) | 30 | 1.36M prompt (0.97M served from cache) / 112k | ~$2.30 | ~60 min |

Wall clock is dominated by lab resets and symptom settle time (18 resets per
sweep), not by the LLM calls. Costs scale with the agent version: the v1
agent burned ~$4.15 for the same 18 rows the v2 agent did for ~$2.56.

**Gotcha we hit:** background sweeps die if the host suspends mid-run
(docker and the harness survive; the runner process does not). Disable
auto-suspend for long sweeps. If a sweep is interrupted, completed rows are
already on disk; finish the missing slices with `--case`/`--repetitions`
and merge, as documented in `results/20260829-v1-agent/results.json` meta.

## Tests and clean-clone validation

```bash
make test       # 64 unit tests: grading, both tool allowlists, cases schema,
                # trajectory writer, renderer, text helpers. No docker, no key.
make validate   # git-archives HEAD into a temp dir, then setup + test + up +
                # smoke + down there, under an isolated compose project/port.
                # Expected last line:
                #   validate: OK (setup, test, up, smoke, down passed from a clean tree)
```
