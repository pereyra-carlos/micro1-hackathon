# micro1 Frontier Engineering Challenge 2026

Solo entry by Carlos Pereyra. Challenge window: Aug 28-31, 2026. Statement drops at kickoff.

## Context

- Everything in this repo is written fresh during the challenge window. Do not copy code from other local projects.
- Agent trajectories (Claude Code transcripts) are part of the submission. Keep every session strictly about this challenge: no personal, client, or infrastructure details, no secrets, no references to other projects.
- The repo goes public at submission time so judges can clone and run it.

## Working conventions

- All code, commits, docs, and comments in English.
- Judging values correct, reproducible, testable, clearly explained work over feature count:
  - Tests for every non-trivial behavior; a single command runs them.
  - `make up` (or equivalent) reproduces the whole thing from a clean clone — Docker if the stack allows it.
  - README explains the problem, the approach, key decisions and trade-offs, and how to run and test.
- Small atomic commits with meaningful messages — the git history is part of the story.
- Never commit secrets or tokens of any kind.
- Never print environment variable values — names only (e.g. when debugging env, use `cut -d= -f1`).
- Never read or reference files outside this repository (no `~/.claude`, no other local projects): the session transcript is part of the submission and must stay free of anything unrelated to the challenge.

## Engineering patterns

- The simplest design that meets the requirement wins. Add complexity only when a requirement demands it, not because it might be needed later.
- When the statement is ambiguous, pick a sensible interpretation and record it as an explicit assumption in the README — never guess silently.
- Build a thin end-to-end slice first (input → core → output, one happy path, one test), then deepen. A working slice beats three half-built layers.
- If a fix fails twice, stop patching and change layers: question the diagnosis, not the bandage.
- Debug from evidence: reproduce the failure, read the actual error, and when something works in one setup but not another, diff the environments before touching config.
- Prove behavior with a canary test — a case that must fail if the feature breaks — rather than by inspecting logs and declaring victory.
- Comments only where the code cannot say it; the README carries the reasoning.

## Delivery checklist (before submitting)

- `make setup && make test && make run` works from a fresh clone in a clean environment (a container if the stack allows).
- README covers: problem, approach, key decisions and trade-offs, explicit assumptions, how to run and test. Anything not tested is declared as such — never imply coverage that does not exist.
- Every edge case named in the statement has a test, or a documented reason why not.
- Re-read the full statement and confirm each requirement is addressed or consciously descoped in writing.
- Tool disclosure in the README: Claude Code, in a two-session setup — a clean build session (this one, whose trajectory is submitted) receiving instructions refined in a separate planning/review session.
