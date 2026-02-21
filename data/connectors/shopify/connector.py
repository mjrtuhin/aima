from typing import Optional
from datetime import datetime
import httpx

from data.connectors.base import BaseConnector, CustomerRecord, OrderRecord, EventRecord, ConnectorRegistry, SyncResult


@ConnectorRegistry.register("shopify")
class ShopifyConnector(BaseConnector):
    connector_type = "shopify"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        super().__init__(org_id, connector_id, config, credentials)
        self.shop_domain = config.get("shop_domain", "")
        self.api_key = credentials.get("api_key", "")
        self.api_secret = credentials.get("api_secret", "")
        self.access_token = credentials.get("access_token", "")
        self.api_version = config.get("api_version", "2024-04")
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"

    @property
    def headers(self) -> dict:
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        try:
            with httpx.Client() as client:
                resp = client.get(f"{self.base_url}/shop.json", headers=self.headers, timeout=10)
                return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        customers = []
        params = {"limit": 250}
        if since:
            params["updated_at_min"] = since.isoformat()

        page_info = None
        while True:
            if page_info:
                params = {"limit": 250, "page_info": page_info}

            with httpx.Client() as client:
                resp = client.get(
                    f"{self.base_url}/customers.json",
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

            for c in data.get("customers", []):
                addr = c.get("default_address") or {}
                customers.append(CustomerRecord(
                    external_id=str(c["id"]),
                    email=c.get("email"),
                    first_name=c.get("first_name"),
                    last_name=c.get("last_name"),
                    phone=c.get("phone"),
                    country=addr.get("country"),
                    city=addr.get("city"),
                    created_at=datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")) if c.get("created_at") else None,
                    properties={
                        "tags": c.get("tags", ""),
                        "accepts_marketing": c.get("accepts_marketing", False),
                        "orders_count": c.get("orders_count", 0),
                        "total_spent": c.get("total_spent", "0"),
                        "verified_email": c.get("verified_email", False),
                        "currency": c.get("currency", "USD"),
                    }
                ))

            link_header = resp.headers.get("Link", "")
            if 'rel="next"' in link_header:
                import re
                match = re.search(r'page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                page_info = match.group(1) if match else None
            else:
                break

        self.log.info("Shopify customers fetched", count=len(customers))
        return customers

    def fetch_orders(self, since: Optional[datetime] = None) -> list[OrderRecord]:
        orders = []
        params = {"limit": 250, "status": "any"}
        if since:
            params["updated_at_min"] = since.isoformat()

        page_info = None
        while True:
            if page_info:
                params = {"limit": 250, "status": "any", "page_info": page_info}

            with httpx.Client() as client:
                resp = client.get(
                    f"{self.base_url}/orders.json",
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

            for o in data.get("orders", []):
                items = []
                for li in o.get("line_items", []):
                    items.append({
                        "product_id": str(li.get("product_id", "")),
                        "variant_id": str(li.get("variant_id", "")),
                        "title": li.get("title", ""),
                        "quantity": li.get("quantity", 1),
                        "price": float(li.get("price", 0)),
                        "sku": li.get("sku", ""),
                        "vendor": li.get("vendor", ""),
                    })

                orders.append(OrderRecord(
                    external_id=str(o["id"]),
                    customer_external_id=str(o["customer"]["id"]) if o.get("customer") else None,
                    total=float(o.get("total_price", 0)),
                    currency=o.get("currency", "USD"),
                    status=o.get("financial_status", "paid"),
                    items=items,
                    discount_total=float(o.get("total_discounts", 0)),
                    channel=o.get("source_name"),
                    ordered_at=datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")) if o.get("created_at") else None,
                    properties={
                        "order_number": o.get("order_number"),
                        "fulfillment_status": o.get("fulfillment_status"),
                        "tags": o.get("tags", ""),
                    }
                ))

            link_header = resp.headers.get("Link", "")
            if 'rel="next"' in link_header:
                import re
                match = re.search(r'page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                page_info = match.group(1) if match else None
            else:
                break

        self.log.info("Shopify orders fetched", count=len(orders))
        return orders
