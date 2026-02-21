from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import structlog

log = structlog.get_logger()


@dataclass
class SyncResult:
    success: bool
    records_synced: int = 0
    records_failed: int = 0
    errors: list[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class CustomerRecord:
    external_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    properties: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class OrderRecord:
    external_id: str
    customer_external_id: Optional[str]
    total: float
    currency: str = "USD"
    status: str = "completed"
    items: list[dict] = field(default_factory=list)
    discount_total: float = 0.0
    channel: Optional[str] = None
    ordered_at: Optional[datetime] = None
    properties: dict = field(default_factory=dict)


@dataclass
class EventRecord:
    customer_external_id: str
    event_type: str
    event_data: dict = field(default_factory=dict)
    source: Optional[str] = None
    occurred_at: Optional[datetime] = None


class BaseConnector(ABC):
    connector_type: str = "base"

    def __init__(self, org_id: str, connector_id: str, config: dict, credentials: dict):
        self.org_id = org_id
        self.connector_id = connector_id
        self.config = config
        self.credentials = credentials
        self.log = log.bind(
            connector_type=self.connector_type,
            connector_id=connector_id,
            org_id=org_id
        )

    @abstractmethod
    def validate_credentials(self) -> bool:
        pass

    @abstractmethod
    def fetch_customers(self, since: Optional[datetime] = None) -> list[CustomerRecord]:
        pass

    @abstractmethod
    def fetch_orders(self, since: Optional[datetime] = None) -> list[OrderRecord]:
        pass

    def fetch_events(self, since: Optional[datetime] = None) -> list[EventRecord]:
        return []

    def sync(self, since: Optional[datetime] = None) -> SyncResult:
        self.log.info("Starting sync", since=since)
        result = SyncResult(success=True)
        try:
            customers = self.fetch_customers(since=since)
            result.records_synced += len(customers)
            self.log.info("Customers fetched", count=len(customers))

            orders = self.fetch_orders(since=since)
            result.records_synced += len(orders)
            self.log.info("Orders fetched", count=len(orders))

            events = self.fetch_events(since=since)
            result.records_synced += len(events)

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.log.error("Sync failed", error=str(e))

        return result


class ConnectorRegistry:
    _registry: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_type: str):
        def decorator(connector_class: type[BaseConnector]):
            cls._registry[connector_type] = connector_class
            return connector_class
        return decorator

    @classmethod
    def get_class(cls, connector_type: str) -> type[BaseConnector]:
        if connector_type not in cls._registry:
            raise ValueError(f"Unknown connector type: {connector_type}. Available: {list(cls._registry.keys())}")
        return cls._registry[connector_type]

    @classmethod
    def list_available(cls) -> list[str]:
        return list(cls._registry.keys())
