from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import StrEnum
from typing import Any


class WorkStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    PASS = "PASS"
    WAIT = "WAIT"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"


class ValidationDecision(StrEnum):
    PASS = "PASS"
    WAIT = "WAIT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ProductOpportunity:
    title: str
    customer_problem: str
    target_customer: str
    expected_selling_price: float
    expected_product_cost: float
    expected_shipping_cost: float
    payment_fee_rate: float = 0.03
    expected_refund_rate: float = 0.05
    expected_cac: float = 0.0
    supplier_name: str = ""
    supplier_product_ref: str = ""
    supplier_evidence: str = ""
    compliance_risk: str = "UNKNOWN"
    shipping_evidence: str = ""
    returns_evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EconomicsResult:
    selling_price: float
    product_cost: float
    shipping_cost: float
    payment_fees: float
    expected_refund_cost: float
    expected_cac: float
    contribution_profit: float
    contribution_margin: float
    break_even_roas: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
