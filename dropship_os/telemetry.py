from __future__ import annotations

import json
import uuid
from .db import Database


def record_agent_run(db: Database, store_id: str, agent_name: str, status: str, work_order_id: str | None = None, **telemetry) -> str:
    run_id = str(uuid.uuid4())
    payload = json.dumps(telemetry, sort_keys=True)
    with db.transaction() as conn:
        conn.execute("INSERT INTO agent_runs(id, store_id, agent_name, work_order_id, status, telemetry) VALUES (?, ?, ?, ?, ?, ?)", (run_id, store_id, agent_name, work_order_id, status, payload))
    return run_id
