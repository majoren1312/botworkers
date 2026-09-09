from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SupplierSnapshot:
    supplier_name: str
    external_ref: str
    product_cost: float
    shipping_cost: float
    processing_time: str | None
    delivery_estimate: str | None
    destinations: tuple[str, ...]
    tracking_available: bool | None
    returns_terms: str | None
    stock_state: str | None
    evidence_ref: str


class SupplierAdapter(Protocol):
    def fetch_product(self, external_ref: str) -> SupplierSnapshot: ...


class StaticSupplierAdapter:
    """Deterministic adapter for imported/test supplier evidence."""
    def __init__(self, snapshots: dict[str, SupplierSnapshot]): self.snapshots = snapshots
    def fetch_product(self, external_ref: str) -> SupplierSnapshot:
        try: return self.snapshots[external_ref]
        except KeyError as exc: raise KeyError(f"supplier product not found: {external_ref}") from exc
