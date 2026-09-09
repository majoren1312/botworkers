from __future__ import annotations

from datetime import datetime, timedelta, timezone
from .db import Database


class ResourceLeaseManager:
    def __init__(self, db: Database): self.db = db

    def acquire(self, store_id: str, resource: str, owner: str, ttl_seconds: int = 60) -> bool:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=max(1, ttl_seconds))
        with self.db.transaction() as conn:
            row = conn.execute("SELECT owner, lease_expires_at FROM resource_leases WHERE store_id=? AND resource=?", (store_id, resource)).fetchone()
            if row:
                current_expiry = datetime.fromisoformat(row["lease_expires_at"])
                if current_expiry > now and row["owner"] != owner:
                    return False
                conn.execute("DELETE FROM resource_leases WHERE store_id=? AND resource=?", (store_id, resource))
            conn.execute("INSERT INTO resource_leases(store_id, resource, owner, lease_expires_at) VALUES (?, ?, ?, ?)", (store_id, resource, owner, expires.isoformat()))
        return True

    def release(self, store_id: str, resource: str, owner: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM resource_leases WHERE store_id=? AND resource=? AND owner=?", (store_id, resource, owner))
