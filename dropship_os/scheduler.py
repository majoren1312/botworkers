from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduledJob:
    name: str
    cadence: str
    purpose: str


DEFAULT_JOBS = (
    ScheduledJob("daily_store_health", "DAILY", "Store, order, supplier, profitability and incident health."),
    ScheduledJob("weekly_portfolio_review", "WEEKLY", "Product, supplier, content, experiment and financial review."),
    ScheduledJob("monthly_security_cost_review", "MONTHLY", "Credentials, dependencies, platform and AI cost review."),
)
