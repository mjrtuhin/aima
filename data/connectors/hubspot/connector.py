"""
HubSpot CRM Connector for AIMA.
Syncs contacts (customers) and deals from HubSpot using the v3 API.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
import httpx

from data.connectors.base import BaseConnector, CustomerRecord, OrderRecord, ConnectorRegistry


@ConnectorRegistry.register("hubspot")
class HubSpotConnector(BaseConnector):
    connector_type = "hubspot"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        super().__init__(org_id, connector_id, config, credentials)
        self.api_key = credentials.get("api_key", "")
        self.access_token = credentials.get("access_token", "")
        self.base_url = "https://api.hubapi.com"

    @property
    def headers(self) -> dict:
        token = self.access_token or self.api_key
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        try:
            with httpx.Client() as client:
                resp = client.get(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=self.headers,
                    params={"limit": 1},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        customers = []
        after = None
        properties = [
            "email", "firstname", "lastname", "phone", "country",
            "city", "hs_lead_status", "lifecyclestage", "createdate",
            "lastmodifieddate", "hs_email_open", "hs_email_click",
            "hs_email_bounce", "total_revenue", "num_associated_deals",
        ]

        while True:
            params: dict = {"limit": 100, "properties": ",".join(properties)}
            if after:
                params["after"] = after
            if since:
                params["filterGroups"] = []

            with httpx.Client() as client:
                resp = client.get(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

            for contact in data.get("results", []):
                props = contact.get("properties", {})
                customers.append(CustomerRecord(
                    external_id=contact["id"],
                    email=props.get("email"),
                    first_name=props.get("firstname"),
                    last_name=props.get("lastname"),
                    phone=props.get("phone"),
                    country=props.get("country"),
                    city=props.get("city"),
                    properties={
                        "lifecycle_stage": props.get("lifecyclestage"),
                        "lead_status": props.get("hs_lead_status"),
                        "total_revenue": props.get("total_revenue"),
                        "deal_count": props.get("num_associated_deals"),
                        "email_opens": props.get("hs_email_open"),
                        "email_clicks": props.get("hs_email_click"),
                    },
                ))

            paging = data.get("paging", {})
            after = paging.get("next", {}).get("after")
            if not after:
                break

        self.log.info("HubSpot contacts fetched", count=len(customers))
        return customers

    def fetch_orders(self, since: Optional[datetime] = None) -> list[OrderRecord]:
        orders = []
        after = None
        properties = [
            "dealname", "amount", "closedate", "dealstage",
            "pipeline", "hubspot_owner_id", "associated_company_id",
        ]

        while True:
            params: dict = {"limit": 100, "properties": ",".join(properties)}
            if after:
                params["after"] = after

            with httpx.Client() as client:
                resp = client.get(
                    f"{self.base_url}/crm/v3/objects/deals",
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

            for deal in data.get("results", []):
                props = deal.get("properties", {})
                amount = float(props.get("amount") or 0)
                if amount <= 0:
                    continue

                close_date = None
                if props.get("closedate"):
                    try:
                        close_date = datetime.fromisoformat(props["closedate"].replace("Z", "+00:00"))
                    except ValueError:
                        pass

                orders.append(OrderRecord(
                    external_id=deal["id"],
                    customer_external_id=None,
                    total=amount,
                    currency="USD",
                    status=props.get("dealstage", "closed"),
                    ordered_at=close_date,
                    properties={
                        "deal_name": props.get("dealname"),
                        "pipeline": props.get("pipeline"),
                    },
                ))

            paging = data.get("paging", {})
            after = paging.get("next", {}).get("after")
            if not after:
                break

        self.log.info("HubSpot deals fetched", count=len(orders))
        return orders
