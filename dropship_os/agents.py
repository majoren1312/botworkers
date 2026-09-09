from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    responsibility: str
    may_write: tuple[str, ...]


AGENTS = {
    "orchestrator": AgentDefinition("orchestrator", "Prioritize work and enforce one-writer resource leases.", ("work_orders", "leases")),
    "product_validator": AgentDefinition("product_validator", "Validate product truth, evidence, compliance gate and economics readiness.", ("evidence", "products")),
    "supplier_intelligence": AgentDefinition("supplier_intelligence", "Maintain supplier evidence and supplier-product records.", ("suppliers", "supplier_products")),
    "unit_economics": AgentDefinition("unit_economics", "Calculate contribution economics and stop-loss facts.", ("prices", "cost_history", "metrics")),
    "shopify_builder": AgentDefinition("shopify_builder", "Create verified Shopify draft products after approval.", ("shopify_products",)),
    "reliability_qa": AgentDefinition("reliability_qa", "Verify external state and raise incidents on mismatches.", ("incidents", "execution_ledger")),
}
