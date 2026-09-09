from __future__ import annotations

import json
import uuid
from dataclasses import asdict

from .approvals import ApprovalEngine
from .db import Database
from .economics import calculate_unit_economics
from .models import ProductOpportunity, WorkStatus
from .shopify import ShopifyAdapter
from .validation import validate_product


class ProductLaunchWorkflow:
    APPROVAL_TYPE = "SHOPIFY_DRAFT_PRODUCT_CREATE"

    def __init__(self, db: Database, shopify: ShopifyAdapter, store_id: str):
        self.db = db
        self.shopify = shopify
        self.store_id = store_id
        self.approvals = ApprovalEngine(db)

    def prepare(self, opportunity: ProductOpportunity) -> dict:
        validation = validate_product(opportunity)
        economics = calculate_unit_economics(opportunity)
        work_order_id, supplier_id, supplier_product_id, product_id = (str(uuid.uuid4()) for _ in range(4))
        status = WorkStatus.READY if validation.decision.value == "PASS" else WorkStatus.WAIT
        with self.db.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO stores(id, owner, state, verification_state) VALUES (?, 'orchestrator', 'BUILDING', 'VERIFIED_LOCAL')", (self.store_id,))
            conn.execute("INSERT INTO suppliers(id, store_id, name, owner, state, evidence, verification_state) VALUES (?, ?, ?, 'supplier_intelligence', 'VALIDATED', ?, 'EVIDENCE_RECORDED')", (supplier_id, self.store_id, opportunity.supplier_name, json.dumps([opportunity.supplier_evidence])))
            conn.execute("INSERT INTO supplier_products(id, store_id, supplier_id, external_ref, product_cost, shipping_cost, owner, state, evidence, verification_state) VALUES (?, ?, ?, ?, ?, ?, 'supplier_intelligence', 'VALIDATED', ?, 'EVIDENCE_RECORDED')", (supplier_product_id, self.store_id, supplier_id, opportunity.supplier_product_ref, opportunity.expected_product_cost, opportunity.expected_shipping_cost, json.dumps([opportunity.supplier_evidence, opportunity.shipping_evidence, opportunity.returns_evidence])))
            conn.execute("INSERT INTO products(id, store_id, title, owner, state, evidence, verification_state) VALUES (?, ?, ?, 'product_validator', ?, ?, ?)", (product_id, self.store_id, opportunity.title, validation.decision.value, json.dumps(opportunity.to_dict()), validation.decision.value))
            conn.execute("INSERT INTO prices(id, store_id, product_id, amount, currency, owner, state, evidence, verification_state) VALUES (?, ?, ?, ?, 'USD', 'unit_economics', 'PROPOSED', ?, 'CALCULATED')", (str(uuid.uuid4()), self.store_id, product_id, opportunity.expected_selling_price, json.dumps(economics.to_dict())))
            conn.execute("INSERT INTO cost_history(id, store_id, product_id, total_cost, currency, owner, state, evidence, verification_state) VALUES (?, ?, ?, ?, 'USD', 'unit_economics', 'ESTIMATED', ?, 'CALCULATED')", (str(uuid.uuid4()), self.store_id, product_id, opportunity.expected_product_cost + opportunity.expected_shipping_cost, json.dumps(economics.to_dict())))
            conn.execute("INSERT INTO work_orders(id, store_id, objective, resource, current_state, desired_state, primary_owner, expected_value, risk, cost, dependencies, acceptance_criteria, rollback_plan, verification_method, status) VALUES (?, ?, ?, ?, ?, ?, 'shopify_builder', ?, 'MEDIUM', 0, ?, ?, ?, ?, ?)", (work_order_id, self.store_id, "Create a verified Shopify draft product from a validated opportunity", f"product:{product_id}", validation.decision.value, "SHOPIFY_DRAFT_VERIFIED", economics.contribution_profit, json.dumps(["product_validation", "supplier_evidence", "unit_economics", "human_approval"]), "Shopify product exists, title matches, and status is DRAFT", "Delete the newly-created draft product manually if needed; no automatic destructive rollback in v0.1", "Read product back through Shopify GraphQL Admin API", status.value))
            conn.execute("INSERT INTO execution_ledger(id, store_id, work_order_id, action, before_state, diff, after_state, verification_state, result) VALUES (?, ?, ?, 'PREPARE_PRODUCT', '{}', ?, ?, ?, ?)", (str(uuid.uuid4()), self.store_id, work_order_id, json.dumps(opportunity.to_dict()), json.dumps(economics.to_dict()), validation.decision.value, "; ".join(validation.reasons) or "validated"))
        approval_id = None
        if validation.decision.value == "PASS":
            approval_id = self.approvals.request(self.store_id, work_order_id, self.APPROVAL_TYPE)
            with self.db.transaction() as conn:
                conn.execute("UPDATE work_orders SET status='WAIT', updated_at=CURRENT_TIMESTAMP WHERE id=?", (work_order_id,))
        return {"work_order_id": work_order_id, "product_id": product_id, "validation": validation.decision.value, "reasons": list(validation.reasons), "economics": economics.to_dict(), "approval_id": approval_id, "status": "WAIT" if approval_id else status.value}

    def execute(self, work_order_id: str) -> dict:
        if not self.approvals.is_approved(work_order_id, self.APPROVAL_TYPE):
            return {"work_order_id": work_order_id, "status": "WAIT", "reason": "human approval required"}
        with self.db.transaction() as conn:
            work = conn.execute("SELECT * FROM work_orders WHERE id=? AND store_id=?", (work_order_id, self.store_id)).fetchone()
            if not work: raise KeyError(f"work order not found: {work_order_id}")
            product_id = work["resource"].split(":", 1)[1]
            product = conn.execute("SELECT * FROM products WHERE id=? AND store_id=?", (product_id, self.store_id)).fetchone()
            if not product: raise KeyError(f"product not found: {product_id}")
            if product["shopify_product_id"]:
                verified = self.shopify.get_product(product["shopify_product_id"])
                if verified and verified.status == "DRAFT" and verified.title == product["title"]:
                    return {"work_order_id": work_order_id, "status": "PASS", "shopify_product_id": verified.id, "idempotent": True}
            conn.execute("UPDATE work_orders SET status='RUNNING', updated_at=CURRENT_TIMESTAMP WHERE id=?", (work_order_id,))
        created = self.shopify.create_draft_product(product["title"])
        with self.db.transaction() as conn:
            conn.execute("UPDATE products SET shopify_product_id=?, state='SHOPIFY_DRAFT_CREATED', updated_at=CURRENT_TIMESTAMP WHERE id=?", (created.id, product_id))
            conn.execute("UPDATE work_orders SET status='VERIFYING', updated_at=CURRENT_TIMESTAMP WHERE id=?", (work_order_id,))
        verified = self.shopify.get_product(created.id)
        passed = bool(verified and verified.id == created.id and verified.title == product["title"] and verified.status == "DRAFT")
        with self.db.transaction() as conn:
            conn.execute("UPDATE products SET state=?, verification_state=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", ("SHOPIFY_DRAFT_VERIFIED" if passed else "VERIFY_FAILED", "PASS" if passed else "FAILED", product_id))
            conn.execute("UPDATE work_orders SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", ("PASS" if passed else "FAILED", work_order_id))
            conn.execute("INSERT INTO execution_ledger(id, store_id, work_order_id, action, before_state, diff, after_state, verification_state, result) VALUES (?, ?, ?, 'SHOPIFY_DRAFT_CREATE', ?, ?, ?, ?, ?)", (str(uuid.uuid4()), self.store_id, work_order_id, json.dumps({"shopify_product_id": None}), json.dumps({"shopify_product_id": created.id}), json.dumps(asdict(verified) if verified else {}), "PASS" if passed else "FAILED", "verified external Shopify draft product" if passed else "external verification mismatch"))
            if not passed:
                conn.execute("INSERT INTO incidents(id, store_id, severity, summary, owner, state, evidence, verification_state) VALUES (?, ?, 'HIGH', ?, 'reliability_qa', 'OPEN', ?, 'VERIFIED')", (str(uuid.uuid4()), self.store_id, f"Shopify product verification failed for {created.id}", json.dumps([asdict(created), asdict(verified) if verified else None])))
        return {"work_order_id": work_order_id, "status": "PASS" if passed else "FAILED", "shopify_product_id": created.id}
