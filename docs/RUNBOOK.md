# Operational Runbook

## Safe execution sequence

1. Read current tenant state.
2. Collect supplier, shipping, returns and compliance evidence.
3. Calculate unit economics.
4. Create a Work Order.
5. If any critical fact is unknown: `WAIT`.
6. If compliance risk is `HIGH`: `REJECT`.
7. Require human approval before the first external Shopify write.
8. Create only a `DRAFT` product.
9. Read it back through Shopify GraphQL.
10. Mark `PASS` only when external ID/title/status match.
11. Record before/diff/after in `execution_ledger`.
12. Raise an incident on verification mismatch.

## Failure handling

- Ambiguous external failure: do not blindly repeat. Read Shopify state first.
- Duplicate execution: verify an existing `shopify_product_id` before creating another product.
- Missing token/scope: `BLOCKED`; do not downgrade the gate.
- Rate limits/transient errors: future retry support must use bounded backoff and verification-before-retry.
- Destructive rollback is intentionally manual in v0.1.

## Security

- Keep tokens in environment variables or a secrets manager.
- Use least privilege and separate credentials per tenant/store.
- Do not place customer data in agent prompts unless required for the specific task.

## Promotion gate for live Shopify testing

Before setting `SHOPIFY_MODE=live`:

- use a development/test store;
- confirm `write_products` scope;
- confirm the store/tenant mapping;
- run all local tests;
- inspect the generated Work Order and economics;
- explicitly approve the Work Order.
