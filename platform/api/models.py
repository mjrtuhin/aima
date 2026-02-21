from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, Numeric, String, Text, ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
import uuid
import enum

from platform.api.database import Base, TimestampMixin


class ConnectorType(str, enum.Enum):
    shopify = "shopify"
    woocommerce = "woocommerce"
    hubspot = "hubspot"
    salesforce = "salesforce"
    klaviyo = "klaviyo"
    mailchimp = "mailchimp"
    activecampaign = "activecampaign"
    meta_ads = "meta_ads"
    google_ads = "google_ads"
    tiktok_ads = "tiktok_ads"
    ga4 = "ga4"
    mixpanel = "mixpanel"
    twitter = "twitter"
    instagram = "instagram"
    csv = "csv"
    postgresql = "postgresql"
    bigquery = "bigquery"
    snowflake = "snowflake"


class CampaignChannel(str, enum.Enum):
    email = "email"
    sms = "sms"
    push = "push"
    meta_ads = "meta_ads"
    google_ads = "google_ads"
    tiktok_ads = "tiktok_ads"
    linkedin_ads = "linkedin_ads"
    display = "display"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    running = "running"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class AlertSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    settings = Column(JSON, default=dict)

    connectors: Mapped[list["Connector"]] = relationship("Connector", back_populates="organization")
    customers: Mapped[list["Customer"]] = relationship("Customer", back_populates="organization")
    campaigns: Mapped[list["Campaign"]] = relationship("Campaign", back_populates="organization")
    segments: Mapped[list["CustomerSegment"]] = relationship("CustomerSegment", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name}>"


class Connector(Base, TimestampMixin):
    __tablename__ = "connectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(ConnectorType), nullable=False)
    name = Column(String(255), nullable=False)
    config = Column(JSON, default=dict)
    credentials_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True))
    sync_frequency_minutes = Column(Integer, default=60)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="connectors")


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255))
    connector_id = Column(UUID(as_uuid=True), ForeignKey("connectors.id"))
    email = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    country = Column(String(100))
    city = Column(String(100))
    timezone = Column(String(50))
    tags = Column(ARRAY(String))
    properties = Column(JSON, default=dict)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="customers")
    features: Mapped[list["CustomerFeatures"]] = relationship("CustomerFeatures", back_populates="customer")
    segment_memberships: Mapped[list["CustomerSegmentMembership"]] = relationship(
        "CustomerSegmentMembership", back_populates="customer"
    )

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)

    def __repr__(self) -> str:
        return f"<Customer id={self.id} email={self.email}>"


class CustomerFeatures(Base):
    __tablename__ = "customer_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    feature_version = Column(Integer, nullable=False, default=1)

    recency_days = Column(Integer)
    frequency = Column(Integer)
    monetary_value = Column(Numeric(12, 2))
    avg_order_value = Column(Numeric(12, 2))
    max_order_value = Column(Numeric(12, 2))
    min_order_value = Column(Numeric(12, 2))
    order_value_std = Column(Numeric(12, 2))
    total_items_purchased = Column(Integer)
    avg_items_per_order = Column(Numeric(8, 2))
    unique_products_count = Column(Integer)
    unique_categories_count = Column(Integer)
    purchase_tenure_days = Column(Integer)
    avg_days_between_purchases = Column(Numeric(8, 2))
    purchase_acceleration = Column(Numeric(8, 4))

    email_open_rate = Column(Numeric(5, 4))
    email_click_rate = Column(Numeric(5, 4))
    email_conversion_rate = Column(Numeric(5, 4))
    cart_abandonment_rate = Column(Numeric(5, 4))
    website_visit_frequency = Column(Numeric(8, 2))
    avg_session_duration_seconds = Column(Integer)

    preferred_day_of_week = Column(Integer)
    preferred_hour_of_day = Column(Integer)
    price_sensitivity_score = Column(Numeric(5, 4))
    brand_loyalty_score = Column(Numeric(5, 4))
    new_product_adoption_rate = Column(Numeric(5, 4))

    customer_health_score = Column(Numeric(5, 2))
    behavioral_vector = Column(ARRAY(Float))

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["Customer"] = relationship("Customer", back_populates="features")


class CustomerSegment(Base, TimestampMixin):
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model_version = Column(String(50))
    cluster_id = Column(Integer)
    customer_count = Column(Integer, default=0)
    avg_health_score = Column(Numeric(5, 2))
    avg_ltv = Column(Numeric(12, 2))
    characteristics = Column(JSON, default=dict)
    recommended_strategy = Column(Text)
    status = Column(String(20), default="active")

    organization: Mapped["Organization"] = relationship("Organization", back_populates="segments")
    memberships: Mapped[list["CustomerSegmentMembership"]] = relationship(
        "CustomerSegmentMembership", back_populates="segment"
    )


class CustomerSegmentMembership(Base):
    __tablename__ = "customer_segment_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id", ondelete="CASCADE"), nullable=False)
    confidence_score = Column(Numeric(5, 4))
    previous_segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["Customer"] = relationship("Customer", back_populates="segment_memberships")
    segment: Mapped["CustomerSegment"] = relationship(
        "CustomerSegment", foreign_keys=[segment_id], back_populates="memberships"
    )


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    channel = Column(Enum(CampaignChannel), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.draft)
    target_segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id"))
    subject_line = Column(String(500))
    preview_text = Column(String(500))
    content = Column(JSON, default=dict)
    offer_type = Column(String(100))
    offer_value = Column(Numeric(8, 2))

    predicted_open_rate = Column(Numeric(5, 4))
    predicted_click_rate = Column(Numeric(5, 4))
    predicted_conversion_rate = Column(Numeric(5, 4))
    predicted_revenue = Column(Numeric(12, 2))
    predicted_roi = Column(Numeric(8, 4))

    actual_open_rate = Column(Numeric(5, 4))
    actual_click_rate = Column(Numeric(5, 4))
    actual_conversion_rate = Column(Numeric(5, 4))
    actual_revenue = Column(Numeric(12, 2))

    budget = Column(Numeric(12, 2))
    scheduled_at = Column(DateTime(timezone=True))
    launched_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    organization: Mapped["Organization"] = relationship("Organization", back_populates="campaigns")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} name={self.name} status={self.status}>"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.medium)
    title = Column(String(500), nullable=False)
    message = Column(Text)
    data = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
