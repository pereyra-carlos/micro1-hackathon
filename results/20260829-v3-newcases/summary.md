# Eval summary

- Model: `claude-sonnet-5`
- Repetitions per case: 3
- Generated: 2026-08-29T14:40:47+00:00

| Case | System | Correct | Component match | Mean wall (s) | Mean tokens in | Mean tokens out |
| --- | --- | --- | --- | --- | --- | --- |
| api-cpu-limit | baseline | 0/3 | 2/3 | 29.0 | 7305 | 2494 |
| api-cpu-limit | agent | 3/3 | 3/3 | 89.0 | 80185 | 4924 |
| nginx-bad-upstream | baseline | 3/3 | 3/3 | 14.7 | 8741 | 1291 |
| nginx-bad-upstream | agent | 3/3 | 3/3 | 20.9 | 26116 | 1646 |
| pg-lock | baseline | 0/3 | 0/3 | 27.8 | 6174 | 2402 |
| pg-lock | agent | 3/3 | 3/3 | 22.0 | 13752 | 1562 |
| redis-auth | baseline | 2/3 | 2/3 | 42.5 | 11589 | 3715 |
| redis-auth | agent | 3/3 | 3/3 | 36.6 | 44052 | 2764 |

- **baseline overall accuracy: 5/12**
- **agent overall accuracy: 12/12**
