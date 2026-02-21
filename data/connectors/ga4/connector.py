"""
Google Analytics 4 Connector for AIMA.
Uses the GA4 Data API to pull website engagement and conversion data.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta
import httpx

from data.connectors.base import BaseConnector, CustomerRecord, OrderRecord, EventRecord, ConnectorRegistry


@ConnectorRegistry.register("ga4")
class GA4Connector(BaseConnector):
    connector_type = "ga4"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        super().__init__(org_id, connector_id, config, credentials)
        self.property_id = config.get("property_id", "")
        self.access_token = credentials.get("access_token", "")
        self.base_url = f"https://analyticsdata.googleapis.com/v1beta/properties/{self.property_id}"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        try:
            payload = {
                "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                "metrics": [{"name": "activeUsers"}],
            }
            with httpx.Client() as client:
                resp = client.post(
                    f"{self.base_url}:runReport",
                    headers=self.headers,
                    json=payload,
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        return []

    def fetch_orders(self, since: Optional[datetime] = None) -> list[OrderRecord]:
        return []

    def fetch_engagement_metrics(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> dict:
        since = since or (datetime.utcnow() - timedelta(days=30))
        until = until or datetime.utcnow()

        payload = {
            "dateRanges": [{
                "startDate": since.strftime("%Y-%m-%d"),
                "endDate": until.strftime("%Y-%m-%d"),
            }],
            "dimensions": [
                {"name": "date"},
                {"name": "sessionSource"},
                {"name": "sessionMedium"},
                {"name": "deviceCategory"},
                {"name": "country"},
            ],
            "metrics": [
                {"name": "sessions"},
                {"name": "activeUsers"},
                {"name": "newUsers"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
                {"name": "screenPageViews"},
                {"name": "conversions"},
                {"name": "totalRevenue"},
                {"name": "ecommercePurchases"},
                {"name": "purchaseRevenue"},
                {"name": "addToCarts"},
                {"name": "checkouts"},
                {"name": "cartToViewRate"},
                {"name": "purchaseToViewRate"},
            ],
            "limit": 10000,
        }

        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}:runReport",
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

        rows = []
        dimension_headers = [h["name"] for h in data.get("dimensionHeaders", [])]
        metric_headers = [h["name"] for h in data.get("metricHeaders", [])]

        for row in data.get("rows", []):
            entry = {}
            for i, dim_val in enumerate(row.get("dimensionValues", [])):
                if i < len(dimension_headers):
                    entry[dimension_headers[i]] = dim_val.get("value")
            for i, met_val in enumerate(row.get("metricValues", [])):
                if i < len(metric_headers):
                    try:
                        entry[metric_headers[i]] = float(met_val.get("value", 0))
                    except ValueError:
                        entry[metric_headers[i]] = 0.0
            rows.append(entry)

        self.log.info("GA4 engagement data fetched", rows=len(rows))
        return {"rows": rows, "row_count": len(rows), "property_id": self.property_id}

    def fetch_page_performance(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[dict]:
        since = since or (datetime.utcnow() - timedelta(days=30))
        until = until or datetime.utcnow()

        payload = {
            "dateRanges": [{
                "startDate": since.strftime("%Y-%m-%d"),
                "endDate": until.strftime("%Y-%m-%d"),
            }],
            "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
            "metrics": [
                {"name": "screenPageViews"},
                {"name": "activeUsers"},
                {"name": "averageSessionDuration"},
                {"name": "bounceRate"},
                {"name": "conversions"},
            ],
            "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
            "limit": 200,
        }

        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}:runReport",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        pages = []
        for row in data.get("rows", []):
            dims = [d.get("value") for d in row.get("dimensionValues", [])]
            mets = [float(m.get("value", 0)) for m in row.get("metricValues", [])]
            pages.append({
                "path": dims[0] if len(dims) > 0 else "",
                "title": dims[1] if len(dims) > 1 else "",
                "views": int(mets[0]) if len(mets) > 0 else 0,
                "users": int(mets[1]) if len(mets) > 1 else 0,
                "avg_session_duration": mets[2] if len(mets) > 2 else 0.0,
                "bounce_rate": mets[3] if len(mets) > 3 else 0.0,
                "conversions": int(mets[4]) if len(mets) > 4 else 0,
            })

        self.log.info("GA4 page performance fetched", pages=len(pages))
        return pages
