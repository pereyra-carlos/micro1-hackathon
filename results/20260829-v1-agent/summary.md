# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-29T02:46:50+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-dns | agent | 1/3 | 3/3 | 226.2 | 226898 | 16680 |
| pg-connections | agent | 2/3 | 2/3 | 67.0 | 84581 | 4353 |
| postgres-down | agent | 3/3 | 3/3 | 44.7 | 41716 | 3196 |
| redis-oom | agent | 2/3 | 2/3 | 115.1 | 105196 | 8663 |
| worker-oom | agent | 3/3 | 3/3 | 21.5 | 18722 | 1516 |
| worker-wrong-queue | agent | 3/3 | 3/3 | 25.5 | 32246 | 1975 |

- **agent overall accuracy: 14/18**
