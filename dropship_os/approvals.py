from __future__ import annotations

import uuid
from .db import Database


class ApprovalEngine:
    def __init__(self, db: Database): self.db = db

    def request(self, store_id: str, work_order_id: str, approval_type: str) -> str:
        approval_id = str(uuid.uuid4())
        with self.db.transaction() as conn:
            conn.execute("INSERT INTO approvals(id, store_id, work_order_id, approval_type, status) VALUES (?, ?, ?, ?, 'PENDING')", (approval_id, store_id, work_order_id, approval_type))
        return approval_id

    def approve(self, approval_id: str, decided_by: str) -> None:
        with self.db.transaction() as conn:
            row = conn.execute("SELECT status FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            if not row: raise KeyError(f"approval not found: {approval_id}")
            if row["status"] != "PENDING": raise ValueError(f"approval is not pending: {row['status']}")
            conn.execute("UPDATE approvals SET status='APPROVED', decided_at=CURRENT_TIMESTAMP, decided_by=? WHERE id=?", (decided_by, approval_id))

    def is_approved(self, work_order_id: str, approval_type: str) -> bool:
        with self.db.connect() as conn:
            row = conn.execute("SELECT 1 FROM approvals WHERE work_order_id=? AND approval_type=? AND status='APPROVED' LIMIT 1", (work_order_id, approval_type)).fetchone()
        return bool(row)
