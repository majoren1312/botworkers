from __future__ import annotations

from dataclasses import dataclass
import json
import urllib.request
import uuid


@dataclass(frozen=True)
class ShopifyProduct:
    id: str
    title: str
    status: str


class ShopifyAdapter:
    def create_draft_product(self, title: str) -> ShopifyProduct: raise NotImplementedError
    def get_product(self, product_id: str) -> ShopifyProduct | None: raise NotImplementedError


class MockShopifyAdapter(ShopifyAdapter):
    def __init__(self): self.products: dict[str, ShopifyProduct] = {}
    def create_draft_product(self, title: str) -> ShopifyProduct:
        product = ShopifyProduct(f"gid://shopify/Product/{uuid.uuid4().int >> 64}", title, "DRAFT")
        self.products[product.id] = product
        return product
    def get_product(self, product_id: str) -> ShopifyProduct | None: return self.products.get(product_id)


class GraphQLShopifyAdapter(ShopifyAdapter):
    def __init__(self, shop_domain: str, access_token: str, api_version: str = "2026-07"):
        self.endpoint = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
        self.access_token = access_token

    def _request(self, query: str, variables: dict) -> dict:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload, headers={"Content-Type": "application/json", "X-Shopify-Access-Token": self.access_token}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("errors"): raise RuntimeError(body["errors"])
        return body["data"]

    def create_draft_product(self, title: str) -> ShopifyProduct:
        query = """mutation CreateDraftProduct($product: ProductCreateInput!) { productCreate(product: $product) { product { id title status } userErrors { field message } } }"""
        data = self._request(query, {"product": {"title": title, "status": "DRAFT"}})["productCreate"]
        if data["userErrors"]: raise RuntimeError(data["userErrors"])
        product = data["product"]
        return ShopifyProduct(product["id"], product["title"], product["status"])

    def get_product(self, product_id: str) -> ShopifyProduct | None:
        query = """query VerifyProduct($id: ID!) { product(id: $id) { id title status } }"""
        product = self._request(query, {"id": product_id})["product"]
        return ShopifyProduct(product["id"], product["title"], product["status"]) if product else None
