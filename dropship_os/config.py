from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    db_path: str = "./dropship_os.db"
    tenant_id: str = "demo-store"
    shopify_shop_domain: str | None = None
    shopify_admin_access_token: str | None = None
    shopify_api_version: str = "2026-07"
    shopify_mode: str = "mock"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=os.getenv("DROPSHIP_DB_PATH", "./dropship_os.db"),
            tenant_id=os.getenv("DROPSHIP_TENANT_ID", "demo-store"),
            shopify_shop_domain=os.getenv("SHOPIFY_SHOP_DOMAIN") or None,
            shopify_admin_access_token=os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN") or None,
            shopify_api_version=os.getenv("SHOPIFY_API_VERSION", "2026-07"),
            shopify_mode=os.getenv("SHOPIFY_MODE", "mock").lower(),
        )
