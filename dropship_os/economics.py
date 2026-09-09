from __future__ import annotations

from .models import EconomicsResult, ProductOpportunity


def calculate_unit_economics(opportunity: ProductOpportunity) -> EconomicsResult:
    price = opportunity.expected_selling_price
    payment_fees = price * opportunity.payment_fee_rate
    expected_refund_cost = price * opportunity.expected_refund_rate
    contribution_profit = price - opportunity.expected_product_cost - opportunity.expected_shipping_cost - payment_fees - expected_refund_cost - opportunity.expected_cac
    contribution_margin = contribution_profit / price if price > 0 else -1.0
    non_ad_contribution = price - opportunity.expected_product_cost - opportunity.expected_shipping_cost - payment_fees - expected_refund_cost
    break_even_roas = price / non_ad_contribution if non_ad_contribution > 0 else None
    return EconomicsResult(
        selling_price=round(price, 2), product_cost=round(opportunity.expected_product_cost, 2), shipping_cost=round(opportunity.expected_shipping_cost, 2),
        payment_fees=round(payment_fees, 2), expected_refund_cost=round(expected_refund_cost, 2), expected_cac=round(opportunity.expected_cac, 2),
        contribution_profit=round(contribution_profit, 2), contribution_margin=round(contribution_margin, 4), break_even_roas=round(break_even_roas, 4) if break_even_roas else None,
    )
