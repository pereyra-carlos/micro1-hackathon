# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-28T21:45:12+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-dns | baseline | 3/3 | 3/3 | 19.1 | 10239 | 1636 |
| api-dns | agent | 1/3 | 3/3 | 191.0 | 227720 | 13972 |
| pg-connections | baseline | 1/3 | 1/3 | 38.7 | 12233 | 3069 |
| pg-connections | agent | 2/3 | 2/3 | 64.4 | 112390 | 4529 |
| postgres-down | baseline | 3/3 | 3/3 | 15.2 | 13361 | 1335 |
| postgres-down | agent | 3/3 | 3/3 | 57.7 | 43014 | 4370 |
| redis-oom | baseline | 2/3 | 2/3 | 39.6 | 7426 | 3498 |
| redis-oom | agent | 3/3 | 3/3 | 66.3 | 52141 | 4818 |
| worker-oom | baseline | 3/3 | 3/3 | 16.6 | 9097 | 1382 |
| worker-oom | agent | 3/3 | 3/3 | 26.9 | 22245 | 1699 |
| worker-wrong-queue | baseline | 0/3 | 3/3 | 21.0 | 10023 | 1711 |
| worker-wrong-queue | agent | 3/3 | 3/3 | 25.8 | 28434 | 1762 |

- **baseline overall accuracy: 12/18**
- **agent overall accuracy: 15/18**
