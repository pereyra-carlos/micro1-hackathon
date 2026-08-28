#!/usr/bin/env bash
# End-to-end smoke test of the healthy lab: every hop must respond.
set -euo pipefail

PORT="${LAB_HTTP_PORT:-18080}"
BASE="http://localhost:${PORT}"

fail() { echo "smoke: FAIL — $1" >&2; exit 1; }

health="$(curl -sf -m 5 "$BASE/health")" || fail "GET /health did not return 200"
echo "$health" | grep -q '"db":"ok"' || fail "api reports db not ok: $health"
echo "$health" | grep -q '"queue":"ok"' || fail "api reports queue not ok: $health"

curl -sf -m 5 "$BASE/orders" | grep -q '"orders"' || fail "GET /orders returned no orders"

job="$(curl -sf -m 5 -X POST "$BASE/jobs")" || fail "POST /jobs failed"
echo "$job" | grep -q '"mode":"queued"' || fail "job was not queued: $job"

# The worker must actually consume the queue: wait for the report to land in
# postgres. This is the canary for the full api -> redis -> worker -> db path.
job_id="$(echo "$job" | sed -E 's/.*"job_id":"([^"]+)".*/\1/')"
for _ in $(seq 1 15); do
    count="$(docker compose -f lab/docker-compose.yml exec -T postgres \
        psql -U app -d shop -At -c "SELECT count(*) FROM reports WHERE job_id = '$job_id'")"
    [ "$count" = "1" ] && { echo "smoke: OK (api, db, queue, worker all healthy)"; exit 0; }
    sleep 1
done
fail "worker never wrote report for job $job_id"
