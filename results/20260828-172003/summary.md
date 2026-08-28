# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-28T17:34:50+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| postgres-down | baseline | 3/3 | 3/3 | 19.8 | 13255 | 1402 |
| postgres-down | agent | 3/3 | 3/3 | 36.0 | 26626 | 2463 |
| redis-oom | baseline | 1/3 | 1/3 | 43.2 | 7310 | 2854 |
| redis-oom | agent | 3/3 | 3/3 | 82.4 | 89819 | 6163 |

- **baseline overall accuracy: 4/6**
- **agent overall accuracy: 6/6**
