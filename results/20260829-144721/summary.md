# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-29T15:46:14+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-cpu-limit | agent | 3/3 | 3/3 | 102.3 | 16 | 6104 |
| api-dns | agent | 3/3 | 3/3 | 143.6 | 13 | 9216 |
| nginx-bad-upstream | agent | 3/3 | 3/3 | 19.0 | 6 | 1495 |
| pg-connections | agent | 3/3 | 3/3 | 38.7 | 11 | 2878 |
| pg-lock | agent | 2/3 | 3/3 | 23.2 | 7 | 1699 |
| postgres-down | agent | 3/3 | 3/3 | 47.2 | 9 | 3547 |
| redis-auth | agent | 3/3 | 3/3 | 30.4 | 9 | 2271 |
| redis-oom | agent | 3/3 | 3/3 | 59.8 | 11 | 4774 |
| worker-oom | agent | 3/3 | 3/3 | 44.8 | 10 | 3062 |
| worker-wrong-queue | agent | 3/3 | 3/3 | 31.5 | 11 | 2189 |

- **agent overall accuracy: 29/30**
