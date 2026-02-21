"""
Meta Ads Connector for AIMA.
Pulls campaign performance data from the Meta (Facebook/Instagram) Marketing API.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta
import httpx

from data.connectors.base import BaseConnector, CustomerRecord, OrderRecord, ConnectorRegistry


@ConnectorRegistry.register("meta_ads")
class MetaAdsConnector(BaseConnector):
    connector_type = "meta_ads"

    GRAPH_API_VERSION = "v19.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        super().__init__(org_id, connector_id, config, credentials)
        self.access_token = credentials.get("access_token", "")
        self.ad_account_id = config.get("ad_account_id", "")
        self.app_id = credentials.get("app_id", "")
        self.app_secret = credentials.get("app_secret", "")

    @property
    def api_url(self) -> str:
        return f"{self.BASE_URL}/{self.GRAPH_API_VERSION}"

    def validate_credentials(self) -> bool:
        try:
            with httpx.Client() as client:
                resp = client.get(
                    f"{self.api_url}/me",
                    params={"access_token": self.access_token, "fields": "id,name"},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        return []

    def fetch_orders(self, since: Optional[datetime] = None) -> list[OrderRecord]:
        return []

    def fetch_campaign_insights(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[dict]:
        since = since or (datetime.utcnow() - timedelta(days=30))
        until = until or datetime.utcnow()

        params = {
            "access_token": self.access_token,
            "fields": ",".join([
                "campaign_name", "campaign_id", "adset_name", "adset_id",
                "impressions", "reach", "clicks", "spend", "cpm", "cpc", "ctr",
                "actions", "action_values", "conversions", "cost_per_conversion",
                "frequency", "unique_clicks", "unique_ctr",
            ]),
            "time_range": f'{{"since":"{since.strftime("%Y-%m-%d")}","until":"{until.strftime("%Y-%m-%d")}"}}',
            "level": "campaign",
            "limit": 500,
        }

        insights = []
        url = f"{self.api_url}/act_{self.ad_account_id}/insights"

        while url:
            with httpx.Client() as client:
                resp = client.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

            for row in data.get("data", []):
                parsed = {
                    "campaign_id": row.get("campaign_id"),
                    "campaign_name": row.get("campaign_name"),
                    "adset_name": row.get("adset_name"),
                    "impressions": int(row.get("impressions", 0)),
                    "reach": int(row.get("reach", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "spend": float(row.get("spend", 0)),
                    "cpm": float(row.get("cpm", 0)),
                    "cpc": float(row.get("cpc", 0)),
                    "ctr": float(row.get("ctr", 0)),
                    "frequency": float(row.get("frequency", 0)),
                    "conversions": 0,
                    "conversion_value": 0.0,
                }
                for action in row.get("actions", []):
                    if action.get("action_type") == "purchase":
                        parsed["conversions"] = int(action.get("value", 0))
                for action_value in row.get("action_values", []):
                    if action_value.get("action_type") == "purchase":
                        parsed["conversion_value"] = float(action_value.get("value", 0))
                insights.append(parsed)

            next_page = data.get("paging", {}).get("next")
            url = next_page if next_page else None
            params = {}

        self.log.info("Meta Ads insights fetched", count=len(insights))
        return insights

    def fetch_audiences(self) -> list[dict]:
        params = {
            "access_token": self.access_token,
            "fields": "id,name,description,approximate_count_lower_bound,approximate_count_upper_bound,subtype",
            "limit": 200,
        }
        url = f"{self.api_url}/act_{self.ad_account_id}/customaudiences"
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        audiences = [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "description": a.get("description"),
                "size_lower": a.get("approximate_count_lower_bound"),
                "size_upper": a.get("approximate_count_upper_bound"),
                "subtype": a.get("subtype"),
            }
            for a in data.get("data", [])
        ]
        self.log.info("Meta Ads audiences fetched", count=len(audiences))
        return audiences
