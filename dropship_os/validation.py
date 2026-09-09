from __future__ import annotations

from dataclasses import dataclass
from .economics import calculate_unit_economics
from .models import ProductOpportunity, ValidationDecision


@dataclass(frozen=True)
class ValidationResult:
    decision: ValidationDecision
    reasons: tuple[str, ...]


def validate_product(opportunity: ProductOpportunity) -> ValidationResult:
    reasons: list[str] = []
    if not opportunity.customer_problem.strip(): reasons.append("customer problem is missing")
    if not opportunity.target_customer.strip(): reasons.append("target customer is missing")
    if not opportunity.supplier_name.strip() or not opportunity.supplier_product_ref.strip(): reasons.append("supplier identity/reference is missing")
    if not opportunity.supplier_evidence.strip(): reasons.append("supplier evidence is missing")
    if not opportunity.shipping_evidence.strip(): reasons.append("shipping evidence is missing")
    if not opportunity.returns_evidence.strip(): reasons.append("returns evidence is missing")
    if opportunity.compliance_risk.upper() in {"HIGH", "UNKNOWN"}: reasons.append(f"compliance risk is {opportunity.compliance_risk.upper()}")
    if calculate_unit_economics(opportunity).contribution_profit <= 0: reasons.append("expected contribution profit is not positive")
    if any("compliance risk is HIGH" in r for r in reasons): return ValidationResult(ValidationDecision.REJECT, tuple(reasons))
    if reasons: return ValidationResult(ValidationDecision.WAIT, tuple(reasons))
    return ValidationResult(ValidationDecision.PASS, ())
