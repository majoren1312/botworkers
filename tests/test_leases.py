from pathlib import Path
import tempfile
import unittest

from dropship_os.db import Database
from dropship_os.leases import ResourceLeaseManager


class LeaseTests(unittest.TestCase):
    def test_one_writer_per_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(str(Path(tmp) / "lease.db")); db.migrate(); leases = ResourceLeaseManager(db)
            self.assertTrue(leases.acquire("store-a", "product:1", "worker-a", ttl_seconds=60))
            self.assertFalse(leases.acquire("store-a", "product:1", "worker-b", ttl_seconds=60))
            leases.release("store-a", "product:1", "worker-a")
            self.assertTrue(leases.acquire("store-a", "product:1", "worker-b", ttl_seconds=60))


if __name__ == "__main__": unittest.main()
