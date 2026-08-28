"""Job processing shared by the worker and the api's synchronous fallback."""

import json
import time

REPORT_CRUNCH_SECONDS = 2.0


def run_job(conn_factory, job):
    """Build a sales report and persist it. Returns the report payload."""
    with conn_factory() as conn:
        (total,) = conn.execute("SELECT count(*) FROM orders").fetchone()
        report = {"orders_total": total, "kind": job.get("kind", "unknown")}
        time.sleep(REPORT_CRUNCH_SECONDS)  # simulated heavy aggregation
        conn.execute(
            "INSERT INTO reports (job_id, payload) VALUES (%s, %s)",
            (job["id"], json.dumps(report)),
        )
        conn.commit()
    return report
