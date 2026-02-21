from typing import Optional
from datetime import datetime
import httpx

from data.connectors.base import BaseConnector, CustomerRecord, EventRecord, ConnectorRegistry


@ConnectorRegistry.register("klaviyo")
class KlaviyoConnector(BaseConnector):
    connector_type = "klaviyo"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        super().__init__(org_id, connector_id, config, credentials)
        self.api_key = credentials.get("api_key", "")
        self.base_url = "https://a.klaviyo.com/api"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Klaviyo-API-Key {self.api_key}",
            "revision": "2024-05-15",
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        try:
            with httpx.Client() as client:
                resp = client.get(f"{self.base_url}/accounts/", headers=self.headers, timeout=10)
                return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        customers = []
        url = f"{self.base_url}/profiles/"
        params = {"page[size]": 100}
        if since:
            params["filter"] = f"greater-than(updated,{since.isoformat()})"

        while url:
            with httpx.Client() as client:
                resp = client.get(url, headers=self.headers, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

            for profile in data.get("data", []):
                attrs = profile.get("attributes", {})
                loc = attrs.get("location", {}) or {}
                customers.append(CustomerRecord(
                    external_id=profile["id"],
                    email=attrs.get("email"),
                    first_name=attrs.get("first_name"),
                    last_name=attrs.get("last_name"),
                    phone=attrs.get("phone_number"),
                    country=loc.get("country"),
                    city=loc.get("city"),
                    properties={
                        "subscriptions": attrs.get("subscriptions", {}),
                        "consent": attrs.get("consent", {}),
                    }
                ))

            url = data.get("links", {}).get("next")
            params = {}

        self.log.info("Klaviyo profiles fetched", count=len(customers))
        return customers

    def fetch_orders(self, since: Optional[datetime] = None) -> list:
        return []

    def fetch_events(self, since: Optional[datetime] = None) -> list[EventRecord]:
        events = []
        url = f"{self.base_url}/events/"
        params = {"page[size]": 100}
        if since:
            params["filter"] = f"greater-than(datetime,{since.isoformat()})"

        while url:
            with httpx.Client() as client:
                resp = client.get(url, headers=self.headers, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

            for event in data.get("data", []):
                attrs = event.get("attributes", {})
                profile_id = (
                    event.get("relationships", {})
                    .get("profile", {})
                    .get("data", {})
                    .get("id", "")
                )
                events.append(EventRecord(
                    customer_external_id=profile_id,
                    event_type=attrs.get("metric_id", "unknown"),
                    event_data=attrs.get("properties", {}),
                    source="klaviyo",
                    occurred_at=datetime.fromisoformat(attrs["datetime"]) if attrs.get("datetime") else None,
                ))

            url = data.get("links", {}).get("next")
            params = {}

        self.log.info("Klaviyo events fetched", count=len(events))
        return events
