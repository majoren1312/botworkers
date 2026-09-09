from __future__ import annotations

import time
from .db import Database


def maintenance_cycle(db: Database) -> dict:
    with db.connect() as conn:
        open_incidents = conn.execute("SELECT COUNT(*) AS n FROM incidents WHERE state='OPEN'").fetchone()["n"]
        waiting_work = conn.execute("SELECT COUNT(*) AS n FROM work_orders WHERE status IN ('WAIT','READY')").fetchone()["n"]
    return {"open_incidents": open_incidents, "waiting_work": waiting_work}


def run_worker(db: Database, interval_seconds: int = 60) -> None:
    while True:
        print(maintenance_cycle(db), flush=True)
        time.sleep(max(1, interval_seconds))
