from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from dropship_os.approvals import ApprovalEngine
from dropship_os.db import Database
from dropship_os.economics import calculate_unit_economics
from dropship_os.models import ProductOpportunity
from dropship_os.shopify import MockShopifyAdapter
from dropship_os.validation import validate_product
from dropship_os.workflow import ProductLaunchWorkflow


def valid_opportunity() -> ProductOpportunity:
    return ProductOpportunity(title="Test Product", customer_problem="Useful test problem", target_customer="Test customer", expected_selling_price=50, expected_product_cost=10, expected_shipping_cost=5, expected_cac=10, supplier_name="Supplier A", supplier_product_ref="sku-1", supplier_evidence="verified supplier page snapshot", compliance_risk="LOW", shipping_evidence="verified shipping terms", returns_evidence="verified returns terms")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.db = Database(str(Path(self.tmp.name) / "test.db")); self.db.migrate(); self.shopify = MockShopifyAdapter(); self.workflow = ProductLaunchWorkflow(self.db, self.shopify, "store-a")
    def tearDown(self): self.tmp.cleanup()
    def test_economics_positive(self): self.assertGreater(calculate_unit_economics(valid_opportunity()).contribution_profit, 0)
    def test_missing_evidence_waits(self):
        o = valid_opportunity(); invalid = ProductOpportunity(**{**o.to_dict(), "shipping_evidence": ""}); self.assertEqual(validate_product(invalid).decision.value, "WAIT")
    def test_high_compliance_risk_rejects(self):
        o = valid_opportunity(); invalid = ProductOpportunity(**{**o.to_dict(), "compliance_risk": "HIGH"}); self.assertEqual(validate_product(invalid).decision.value, "REJECT")
    def test_approval_gate_and_verified_shopify_draft(self):
        prepared = self.workflow.prepare(valid_opportunity()); self.assertEqual(prepared["validation"], "PASS"); self.assertEqual(prepared["status"], "WAIT")
        self.assertEqual(self.workflow.execute(prepared["work_order_id"])["status"], "WAIT")
        ApprovalEngine(self.db).approve(prepared["approval_id"], "tester")
        result = self.workflow.execute(prepared["work_order_id"]); self.assertEqual(result["status"], "PASS")
        replay = self.workflow.execute(prepared["work_order_id"]); self.assertTrue(replay["idempotent"])
        with self.db.connect() as conn:
            work = conn.execute("SELECT status FROM work_orders WHERE id=?", (prepared["work_order_id"],)).fetchone(); ledger = conn.execute("SELECT verification_state FROM execution_ledger WHERE work_order_id=? ORDER BY created_at DESC LIMIT 1", (prepared["work_order_id"],)).fetchone()
        self.assertEqual(work["status"], "PASS"); self.assertEqual(ledger["verification_state"], "PASS")


if __name__ == "__main__": unittest.main()
