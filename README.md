# Multi-Agent Dropshipping OS

Local-first execution core for a reusable, multi-store dropshipping operating system.

## Current verified vertical slice

`PRODUCT OPPORTUNITY → VALIDATION → SUPPLIER RECORD → UNIT ECONOMICS → HUMAN APPROVAL → SHOPIFY DRAFT PRODUCT → EXTERNAL READ-BACK VERIFICATION → EXECUTION LEDGER`

The repository intentionally starts with a small number of real capabilities instead of placeholder agents.

## Design laws

- Verified external state beats agent self-reporting.
- Critical unknowns produce `WAIT`, not `PASS`.
- `HIGH` compliance risk produces `REJECT`.
- Shopify creation is draft-only in v0.1.
- A human approval is required before the Shopify write.
- External writes use an idempotent replay check before creating another product.
- Every tenant/store is keyed by `store_id`; credentials are configuration-scoped and must not be committed.
- SQLite is the local default to keep development inexpensive.
- Deterministic work uses deterministic Python code. AI is not required for calculations, state transitions, approvals or verification.

## Run locally

Requires Python 3.11+.

```bash
python -m unittest discover -s tests -v
python -m dropship_os.cli init-db
python -m dropship_os.cli demo
```

The `demo` command prepares a validated work order and prints its `approval_id` and `work_order_id`.

```bash
python -m dropship_os.cli approve <approval_id> --by owner
python -m dropship_os.cli execute <work_order_id>
```

By default `SHOPIFY_MODE=mock`, so no real store is changed.

## Live Shopify mode

Use a dedicated development/test store first.

```bash
export SHOPIFY_MODE=live
export SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
export SHOPIFY_ADMIN_ACCESS_TOKEN=...
export SHOPIFY_API_VERSION=2026-07
python -m dropship_os.cli execute <approved_work_order_id>
```

The live adapter uses Shopify GraphQL Admin API `productCreate` with `status: DRAFT`, then queries the product by ID and requires ID/title/status to match before the Work Order becomes `PASS`. The token requires Shopify `write_products`. Never commit the token.

## Local API

```bash
python -m dropship_os.cli serve --port 8080
```

Endpoints: `GET /health`, `GET /work-orders`, `GET /incidents`.

## Persistent state

`migrations/001_init.sql` creates tenant-scoped tables for stores, brands, products, variants, suppliers, supplier products, markets, catalogs, prices, cost history, inventory, orders, fulfillments, customers, support cases, experiments, content, campaigns, metrics, incidents, work orders, resource leases, agent runs, approvals, evidence and the execution ledger.

## Next vertical slices

1. Enforced resource leases with expiry/renewal and optimistic version checks.
2. Real supplier adapter interface + supplier evidence snapshots.
3. Product variant/price write after draft creation, with verification.
4. Store launch gate and Shopify Markets/catalog verification.
5. Order/fulfillment event ingestion and incident handling.
6. Only after these are reliable: opportunity discovery, SEO/CRO/acquisition agents and multi-store portfolio intelligence.

See `docs/RUNBOOK.md` for operating rules.
