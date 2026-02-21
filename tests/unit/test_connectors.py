"""
Unit tests for data connectors.
Tests the base connector interface and connector registry.
"""

import pytest
from datetime import datetime
from data.connectors.base import (
    BaseConnector, ConnectorRegistry, SyncResult,
    CustomerRecord, OrderRecord, EventRecord
)


class MockConnector(BaseConnector):
    connector_type = "mock"

    def validate_credentials(self) -> bool:
        return True

    def fetch_customers(self, since=None) -> list[CustomerRecord]:
        return [
            CustomerRecord(external_id="C1", email="a@example.com", first_name="Alice"),
            CustomerRecord(external_id="C2", email="b@example.com", first_name="Bob"),
        ]

    def fetch_orders(self, since=None) -> list[OrderRecord]:
        return [
            OrderRecord(external_id="O1", customer_external_id="C1", total=99.0),
        ]


@pytest.fixture
def connector():
    return MockConnector(
        org_id="org-1",
        connector_id="conn-1",
        config={},
        credentials={},
    )


class TestBaseConnector:
    def test_validate_credentials_returns_bool(self, connector):
        assert isinstance(connector.validate_credentials(), bool)

    def test_fetch_customers_returns_list(self, connector):
        result = connector.fetch_customers()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_customer_record_has_external_id(self, connector):
        customers = connector.fetch_customers()
        for c in customers:
            assert hasattr(c, "external_id")
            assert c.external_id is not None

    def test_fetch_orders_returns_list(self, connector):
        result = connector.fetch_orders()
        assert isinstance(result, list)

    def test_sync_returns_sync_result(self, connector):
        result = connector.sync()
        assert isinstance(result, SyncResult)
        assert result.success is True
        assert result.records_synced > 0

    def test_sync_counts_customers_and_orders(self, connector):
        result = connector.sync()
        assert result.records_synced == 3

    def test_fetch_events_returns_empty_by_default(self, connector):
        events = connector.fetch_events()
        assert isinstance(events, list)
        assert len(events) == 0


class TestConnectorRegistry:
    def test_register_and_retrieve(self):
        @ConnectorRegistry.register("test_mock_unique")
        class TestMock(MockConnector):
            connector_type = "test_mock_unique"

        cls = ConnectorRegistry.get_class("test_mock_unique")
        assert cls is TestMock

    def test_unknown_connector_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown connector type"):
            ConnectorRegistry.get_class("does_not_exist_xyz")

    def test_list_available_returns_list(self):
        available = ConnectorRegistry.list_available()
        assert isinstance(available, list)
        assert "shopify" in available
        assert "klaviyo" in available


class TestDataclasses:
    def test_customer_record_creation(self):
        c = CustomerRecord(external_id="X1", email="test@test.com")
        assert c.external_id == "X1"
        assert c.email == "test@test.com"
        assert c.properties == {}

    def test_order_record_creation(self):
        o = OrderRecord(external_id="O1", customer_external_id="C1", total=150.0)
        assert o.total == 150.0
        assert o.currency == "USD"
        assert o.items == []

    def test_sync_result_defaults(self):
        r = SyncResult(success=True)
        assert r.records_synced == 0
        assert r.errors == []
