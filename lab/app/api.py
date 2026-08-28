import json
import logging
import os
import time
import uuid

import psycopg
import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from processing import run_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("api")

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
QUEUE_KEY = "jobs"

app = FastAPI()
rdb = redis.Redis.from_url(
    REDIS_URL, socket_timeout=2, socket_connect_timeout=2, decode_responses=True
)


def db_conn():
    return psycopg.connect(DATABASE_URL, connect_timeout=2)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    ms = (time.monotonic() - start) * 1000
    log.info("%s %s -> %d %.0fms", request.method, request.url.path, response.status_code, ms)
    return response


@app.get("/health")
def health():
    status, code = {"db": "ok", "queue": "ok"}, 200
    try:
        with db_conn() as conn:
            conn.execute("SELECT 1")
    except Exception:
        status["db"], code = "unreachable", 503
    try:
        rdb.ping()
    except Exception:
        status["queue"], code = "unreachable", 503
    return JSONResponse(status, status_code=code)


@app.get("/orders")
def orders():
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT id, item, status FROM orders ORDER BY id DESC LIMIT 10"
        ).fetchall()
    return {"orders": [{"id": r[0], "item": r[1], "status": r[2]} for r in rows]}


@app.post("/jobs")
def submit_job():
    job = {"id": uuid.uuid4().hex[:12], "kind": "sales_report"}
    try:
        rdb.rpush(QUEUE_KEY, json.dumps(job))
        return JSONResponse({"job_id": job["id"], "mode": "queued"}, status_code=202)
    except redis.RedisError as exc:
        # Graceful degradation: keep serving requests even if the queue is
        # unavailable, at the cost of doing the work inline.
        log.debug("enqueue failed (%s), processing synchronously", exc)
        result = run_job(db_conn, job)
        return {"job_id": job["id"], "mode": "sync", "result": result}
