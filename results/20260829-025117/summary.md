# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-29T03:27:11+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-dns | agent | 3/3 | 3/3 | 129.9 | 98706 | 7587 |
| pg-connections | agent | 3/3 | 3/3 | 65.9 | 92662 | 4535 |
| postgres-down | agent | 3/3 | 3/3 | 52.7 | 50491 | 3540 |
| redis-oom | agent | 3/3 | 3/3 | 38.4 | 24654 | 2969 |
| worker-oom | agent | 3/3 | 3/3 | 24.7 | 21957 | 1586 |
| worker-wrong-queue | agent | 3/3 | 3/3 | 27.2 | 27199 | 1941 |

- **agent overall accuracy: 18/18**
