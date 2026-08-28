import json
import logging
import os
import time

import psycopg
import redis

from processing import run_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
QUEUE_KEY = os.environ.get("QUEUE_KEY", "jobs")


def db_conn():
    return psycopg.connect(DATABASE_URL, connect_timeout=2)


def main():
    rdb = redis.Redis.from_url(
        REDIS_URL, socket_timeout=10, socket_connect_timeout=2, decode_responses=True
    )
    log.info("worker started")
    while True:
        try:
            item = rdb.blpop(QUEUE_KEY, timeout=5)
            if item is None:
                continue
            job = json.loads(item[1])
            start = time.monotonic()
            run_job(db_conn, job)
            log.info("processed job %s in %.1fs", job["id"], time.monotonic() - start)
        except Exception:
            log.exception("job processing failed, retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
