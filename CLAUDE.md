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
