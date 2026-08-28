# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-28T20:50:40+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-dns | baseline | 3/3 | 3/3 | 28.1 | 10103 | 2338 |
| api-dns | agent | 1/3 | 3/3 | 178.8 | 183698 | 13071 |
| pg-connections | baseline | 1/3 | 1/3 | 23.2 | 12563 | 1941 |
| pg-connections | agent | 0/3 | 0/3 | 52.4 | 52969 | 4022 |
| postgres-down | baseline | 3/3 | 3/3 | 16.3 | 13243 | 1380 |
| postgres-down | agent | 3/3 | 3/3 | 35.5 | 31938 | 2552 |
| redis-oom | baseline | 2/3 | 2/3 | 33.0 | 7295 | 2942 |
| redis-oom | agent | 3/3 | 3/3 | 81.9 | 76049 | 5789 |
| worker-oom | baseline | 3/3 | 3/3 | 78.8 | 17577 | 6427 |
| worker-oom | agent | 3/3 | 3/3 | 41.5 | 42618 | 2783 |
| worker-wrong-queue | baseline | 0/3 | 3/3 | 24.5 | 9905 | 1517 |
| worker-wrong-queue | agent | 3/3 | 3/3 | 27.5 | 32435 | 1841 |

- **baseline overall accuracy: 12/18**
- **agent overall accuracy: 13/18**
