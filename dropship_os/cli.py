from __future__ import annotations

import argparse
import json
import sys

from .api import serve
from .approvals import ApprovalEngine
from .config import Settings
from .db import Database
from .models import ProductOpportunity
from .shopify import GraphQLShopifyAdapter, MockShopifyAdapter
from .workflow import ProductLaunchWorkflow


def build_shopify(settings: Settings):
    if settings.shopify_mode == "live":
        if not settings.shopify_shop_domain or not settings.shopify_admin_access_token:
            raise SystemExit("SHOPIFY_MODE=live requires SHOPIFY_SHOP_DOMAIN and SHOPIFY_ADMIN_ACCESS_TOKEN")
        return GraphQLShopifyAdapter(settings.shopify_shop_domain, settings.shopify_admin_access_token, settings.shopify_api_version)
    return MockShopifyAdapter()


def demo_opportunity() -> ProductOpportunity:
    return ProductOpportunity(title="Validated Demo Product", customer_problem="Provides a simple example product for the verified execution slice.", target_customer="Development/test operator", expected_selling_price=49.0, expected_product_cost=15.0, expected_shipping_cost=5.0, expected_cac=8.0, supplier_name="Demo Supplier", supplier_product_ref="demo-001", supplier_evidence="local demo supplier record", compliance_risk="LOW", shipping_evidence="local demo shipping evidence", returns_evidence="local demo returns evidence")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dropship-os")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    sub.add_parser("demo")
    approve = sub.add_parser("approve"); approve.add_argument("approval_id"); approve.add_argument("--by", default="human-owner")
    execute = sub.add_parser("execute"); execute.add_argument("work_order_id")
    serve_parser = sub.add_parser("serve"); serve_parser.add_argument("--host", default="127.0.0.1"); serve_parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    settings = Settings.from_env(); db = Database(settings.db_path); db.migrate()
    if args.command == "init-db": print(json.dumps({"status": "PASS", "db": settings.db_path})); return 0
    if args.command == "approve": ApprovalEngine(db).approve(args.approval_id, args.by); print(json.dumps({"status": "APPROVED", "approval_id": args.approval_id})); return 0
    if args.command == "demo": print(json.dumps(ProductLaunchWorkflow(db, build_shopify(settings), settings.tenant_id).prepare(demo_opportunity()), indent=2)); return 0
    if args.command == "execute": print(json.dumps(ProductLaunchWorkflow(db, build_shopify(settings), settings.tenant_id).execute(args.work_order_id), indent=2)); return 0
    if args.command == "serve": serve(db, args.host, args.port); return 0
    return 1


if __name__ == "__main__": sys.exit(main())
