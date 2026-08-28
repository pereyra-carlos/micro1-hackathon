# incident-copilot

Solo entry by Carlos Pereyra — micro1 Agentic Workflows Hackathon, Aug 28–31, 2026.

An agentic workflow that takes an infrastructure alert and delivers an
evidence-backed root-cause diagnosis, measured against a fair single-prompt
baseline on a reproducible synthetic incident lab.

## Problem

On-call engineers receive alerts that describe **symptoms** ("API latency
high"), never **causes** ("connection pool exhausted after yesterday's deploy
lowered the limit"). Bridging that gap is 20–40 minutes of investigation under
pressure, and that time is the core of MTTR.

- **User:** the on-call SRE.
- **Deliverable:** a root cause with cited evidence and a suggested fix,
  produced while they are still opening their laptop.
- **Bottleneck attacked:** the investigation loop — hypothesize, check a
  dependency, read the actual state, repeat. That loop is exactly what an
  agent with read-only tools can run autonomously.

## Approach

```
alert ──► baseline: ONE Claude call over a standard evidence dump ──► diagnosis
      └─► agent:    tool-use loop (get_status / get_logs / exec_readonly) ──► diagnosis
                                    both graded against cases.yaml ground truth
```

1. **Lab** (`lab/`): a docker-compose synthetic environment — nginx → FastAPI
   api → postgres, redis used as a queue, a worker consuming it and writing
   reports to postgres, plus a load generator so faults produce live
   symptoms. Services are tiny but real: actual HTTP calls, SQL, queue
   consumption, so faults propagate across services.
2. **Fault injector** (`cases/cases.yaml` + `make break CASE=<id>`): each case
   defines injection commands, the alert text handed to both systems, and the
   canonical root cause as a structured label (component + fault_type enum).
3. **Baseline** (`baseline/`): one Claude API call — same model as the agent,
   a well-written prompt, and the standard evidence dump (`docker compose ps`
   + last 200 log lines of every service + the alert). **Frozen after day 1**;
   it is never improved later.
4. **Agent** (`agent/`): a minimal tool-use loop with read-only tools. Every
   step is appended to `trajectories/<case>/<run-id>.jsonl`. The suggested fix
   is only suggested — never executed (human-approval boundary).
5. **Eval harness** (`eval/`): resets the lab, injects the fault, runs both
   systems against the same broken instance, grades the structured enums
   against ground truth, and records accuracy, wall-clock and tokens into
   `results/`.

## Eval design (pre-registered before any iteration)

This section and the harness were committed **before** the first eval run;
the git history is the pre-registration evidence.

- **Cases (eval set v2, frozen 2026-08-28):** six cases, each verified live
  at design time (symptom present, evidence reachable by the agent's tools,
  and absent or misleading in the dump where intended). At least half are
  unsolvable from the initial evidence dump alone; two pairs share identical
  alert text so the alert never identifies the case.

  | Case | Root cause (component/type) | Solvable from dump? |
  | --- | --- | --- |
  | postgres-down | postgres / process_down | yes — control |
  | pg-connections | postgres / resource_exhaustion | yes — control ("connection slots are reserved" in api logs; leaked sessions attributable via break-glass pg_stat_activity) |
  | api-dns | api / network | misleading — api logs mimic postgres-down; postgres is healthy |
  | redis-oom | redis / resource_exhaustion | no — no service log contains the cause |
  | worker-oom | worker / resource_exhaustion | no — SIGKILL leaves no log; cause only in docker inspect |
  | worker-wrong-queue | worker / misconfiguration | no — worker Up and silent; drift only in inspect Env / redis keys |
- **Metric:** a diagnosis is **correct** iff `root_cause_component` matches
  ground truth exactly AND `root_cause_type` is in the case's declared
  `accepted_fault_types`. Component-only accuracy is also recorded.
- **Repetitions:** N=3 per case per system, full lab reset between
  repetitions. Baseline runs first, then the agent, against the same broken
  instance (faults are steady-state, so order is immaterial).
- **Fairness:** same model (`ANTHROPIC_MODEL`, default `claude-sonnet-5`),
  same `max_tokens`, same structured answer tool with the same schema and the
  same advisory-fix framing. The baseline prompt was written to be genuinely
  good, then frozen.
- **Also recorded:** wall-clock seconds and token usage (input/output) per
  run, so accuracy gains are priced.

## Improvement Changelog

| Version | Change | postgres-down (agent) | redis-oom (agent) | Overall agent | Overall baseline |
| --- | --- | --- | --- | --- | --- |
| v0 | Initial agent, pre-registered eval | 3/3 | 3/3 | **6/6** | 4/6 |

| v0 + psql-tool fix | Eval set v2: 6 cases (4 new), frozen | _running_ | _running_ | _running_ | _running_ |

First full run (eval set v1, 2 cases): `results/20260828-172003/`
(model `claude-sonnet-5`, N=3).
The baseline aces the single-hop control (3/3) but goes 1/3 on the multi-hop
case, twice misattributing the latency to an api code bug; the agent found
the redis misconfiguration in all six runs, at ~2× the wall-clock and ~4×
the tokens of the baseline. Per-run detail, including one baseline run that
correctly guessed redis from the dump's silences, is in `results.json`;
every agent investigation is replayable from `trajectories/`.

## Key decisions and trade-offs

| Decision | Alternative considered | Why |
| --- | --- | --- |
| Multi-hop fault surfaces as latency via the api's silent sync-fallback path | The brief's sketch (worker crashes on redis writes, queue backs up) | In the sketch, the worker's OOM traceback lands in the 200-line dump, so the "requires investigation" property collapses. Graceful degradation that masks the cause is both realistic and makes the multi-hop case genuinely unsolvable from the dump. |
| Answers via a forced-schema `submit_diagnosis` tool (strict enums) | Free-text JSON parsing | Grading needs exact enums; strict tool schemas make malformed answers impossible instead of handled. |
| Manual tool-use loop (~90 lines) | SDK beta tool-runner helper | The loop IS the deliverable being evaluated; owning it gives exact control over trajectory logging and budget enforcement, and avoids a beta dependency. |
| `exec_readonly` = pure validator + shell-free execution + grant-limited DB role | Prompt-level "please be safe" or regex-only filtering | Defense in depth: allowlist is unit-tested as a security boundary, subprocesses never touch a shell, and even a SELECT that sneaks a write hits a role with no write grants. |
| Grading accepts declared fault-type synonyms per case | Single exact enum | redis-at-maxmemory is legitimately both `resource_exhaustion` and `misconfiguration`; forcing one would grade correct diagnoses as wrong. Component match stays exact. |
| Validation = `git archive HEAD` → temp dir → setup/test/up/smoke/down | Container-in-container sandbox | The stack is compose-based; validating on the committed tree from a clean dir proves a judge's clone works without docker-in-docker. |

## Explicit assumptions

- The brief asked for "temperature low": current Claude models reject
  sampling parameters entirely (HTTP 400), so none is set. Both systems use
  identical model settings; run-to-run variance is handled by N=3.
- "Redis misconfigured" is implemented as a grown session cache +
  `maxmemory 8mb` + `noeviction` (writes denied) rather than the sketch's
  worker-write failure — see the first trade-off above. The api's silent
  fallback (`log.debug`, not visible at INFO) is a deliberate lab design
  choice representing fallback paths that mask root causes in real systems.
- `make run CASE=<id>` runs the *agent* on the current (presumably broken)
  lab — the agent is "the application". The full experiment is `make eval`.
- The lab's hardcoded passwords are synthetic fixtures, not secrets.
- Agent budget: at most 12 LLM calls per run; at the last step it is told to
  commit to a diagnosis.

## Getting started

### Requirements

- Docker with the compose plugin (tested: Docker 29 / Compose v5), Python 3.10+.
- `ANTHROPIC_API_KEY` exported (or in a repo-root `.env`, which is
  gitignored) — needed only for baseline/agent/eval, not for tests or the lab.
- Optional: `ANTHROPIC_MODEL` (default `claude-sonnet-5`), `LAB_HTTP_PORT`
  (default 18080).

### Run

```bash
make setup                  # venv + host-side deps
make up                     # start the synthetic lab (healthy state)
make smoke                  # end-to-end canary of the healthy lab
make break CASE=redis-oom   # inject a fault (postgres-down | redis-oom)
make run CASE=redis-oom     # agent diagnoses the broken lab (needs API key)
make eval                   # full experiment: N=3 × cases × {baseline, agent}
make reset                  # deterministic clean state (down -v && up)
```

### Test

```bash
make test      # unit suite: grading, allowlist boundary, cases schema, helpers
make validate  # proves a clean clone works: setup+test+up+smoke+down in a temp dir
```

What is deliberately **not** covered by automated tests: the fault injections
themselves and the LLM calls (they need a live broken lab and an API key).
Fault symptoms were verified manually at design time (documented in the
commit history) and are re-exercised by every eval run; `scripts/smoke.sh` is
the automated canary for the healthy path.

## Project layout

```
lab/        docker-compose stack: nginx, api, worker, postgres, redis, loadgen
cases/      cases.yaml — injections, alerts, ground-truth labels
baseline/   frozen single-call baseline + standard evidence dump
agent/      tool-use loop, read-only tools, trajectory writer
eval/       harness + grading
tests/      unit suite (no docker, no API key needed)
scripts/    break.py, smoke.sh, validate.sh
trajectories/  one JSONL per agent run (committed: part of the submission)
results/    eval outputs: results.json + summary.md per run (committed)
```

## Tooling disclosure

Built with Claude Code in a two-session setup: a clean build session (whose
trajectory is part of the submission) receiving instructions refined in a
separate planning/review session.

## Status

Day 1 complete: lab, two cases, frozen baseline, agent v0, pre-registered
eval harness, and the first full eval run (agent 6/6 vs baseline 4/6).
Later days iterate on the agent only — more cases (at least half unsolvable
from the dump), agent improvements, one changelog row per change.
