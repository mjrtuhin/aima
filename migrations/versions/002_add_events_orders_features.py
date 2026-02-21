"""Add customer_events, orders, customer_features, customer_segment_memberships tables.

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "orders" not in existing_tables:
        op.create_table(
            "orders",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("org_id", sa.String(255), nullable=False),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("external_id", sa.String(255), nullable=True),
            sa.Column("status", sa.String(50), nullable=True),
            sa.Column("currency", sa.String(10), nullable=True),
            sa.Column("subtotal", sa.Numeric(12, 2), nullable=True),
            sa.Column("discount_amount", sa.Numeric(12, 2), nullable=True),
            sa.Column("tax_amount", sa.Numeric(12, 2), nullable=True),
            sa.Column("shipping_amount", sa.Numeric(12, 2), nullable=True),
            sa.Column("total", sa.Numeric(12, 2), nullable=True),
            sa.Column("item_count", sa.Integer, nullable=True),
            sa.Column("line_items", postgresql.JSONB, nullable=True),
            sa.Column("channel", sa.String(50), nullable=True),
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_orders_org_id", "orders", ["org_id"])
        op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
        op.create_index("ix_orders_ordered_at", "orders", ["ordered_at"])
        op.create_index("ix_orders_org_ordered_at", "orders", ["org_id", "ordered_at"])

    op.execute(sa.text("SAVEPOINT sp_ht_orders"))
    try:
        op.execute(sa.text("SELECT create_hypertable('orders', 'created_at', if_not_exists => TRUE, migrate_data => TRUE)"))
        op.execute(sa.text("RELEASE SAVEPOINT sp_ht_orders"))
    except Exception:
        op.execute(sa.text("ROLLBACK TO SAVEPOINT sp_ht_orders"))

    if "customer_events" not in existing_tables:
        op.create_table(
            "customer_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("org_id", sa.String(255), nullable=False),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", sa.String(255), nullable=True),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("event_source", sa.String(100), nullable=True),
            sa.Column("page_url", sa.Text, nullable=True),
            sa.Column("product_id", sa.String(255), nullable=True),
            sa.Column("revenue", sa.Numeric(10, 2), nullable=True),
            sa.Column("metadata", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_customer_events_org_id", "customer_events", ["org_id"])
        op.create_index("ix_customer_events_customer_id", "customer_events", ["customer_id"])
        op.create_index("ix_customer_events_event_type", "customer_events", ["event_type"])
        op.create_index("ix_customer_events_org_created_at", "customer_events", ["org_id", "created_at"])

    op.execute(sa.text("SAVEPOINT sp_ht_customer_events"))
    try:
        op.execute(sa.text("SELECT create_hypertable('customer_events', 'created_at', if_not_exists => TRUE, migrate_data => TRUE)"))
        op.execute(sa.text("RELEASE SAVEPOINT sp_ht_customer_events"))
    except Exception:
        op.execute(sa.text("ROLLBACK TO SAVEPOINT sp_ht_customer_events"))

    if "customer_features" not in existing_tables:
        op.create_table(
            "customer_features",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("org_id", sa.String(255), nullable=False),
            sa.Column("recency_days", sa.Float, nullable=True),
            sa.Column("frequency_30d", sa.Float, nullable=True),
            sa.Column("frequency_90d", sa.Float, nullable=True),
            sa.Column("frequency_365d", sa.Float, nullable=True),
            sa.Column("monetary_30d", sa.Float, nullable=True),
            sa.Column("monetary_90d", sa.Float, nullable=True),
            sa.Column("monetary_365d", sa.Float, nullable=True),
            sa.Column("monetary_total", sa.Float, nullable=True),
            sa.Column("avg_order_value", sa.Float, nullable=True),
            sa.Column("order_value_std", sa.Float, nullable=True),
            sa.Column("max_order_value", sa.Float, nullable=True),
            sa.Column("min_order_value", sa.Float, nullable=True),
            sa.Column("inter_purchase_time_avg", sa.Float, nullable=True),
            sa.Column("inter_purchase_time_std", sa.Float, nullable=True),
            sa.Column("category_diversity", sa.Float, nullable=True),
            sa.Column("discount_usage_rate", sa.Float, nullable=True),
            sa.Column("return_rate", sa.Float, nullable=True),
            sa.Column("total_sessions", sa.Float, nullable=True),
            sa.Column("avg_session_duration", sa.Float, nullable=True),
            sa.Column("page_views_per_session", sa.Float, nullable=True),
            sa.Column("cart_abandonment_rate", sa.Float, nullable=True),
            sa.Column("email_open_rate", sa.Float, nullable=True),
            sa.Column("email_click_rate", sa.Float, nullable=True),
            sa.Column("email_unsubscribe_rate", sa.Float, nullable=True),
            sa.Column("push_open_rate", sa.Float, nullable=True),
            sa.Column("preferred_hour", sa.Float, nullable=True),
            sa.Column("preferred_day", sa.Float, nullable=True),
            sa.Column("weekend_purchase_rate", sa.Float, nullable=True),
            sa.Column("trend_monetary_90d", sa.Float, nullable=True),
            sa.Column("trend_frequency_90d", sa.Float, nullable=True),
            sa.Column("engagement_score", sa.Float, nullable=True),
            sa.Column("spend_trend", sa.Float, nullable=True),
            sa.Column("health_score", sa.Float, nullable=True),
            sa.Column("behavioral_vector", postgresql.ARRAY(sa.Float), nullable=True),
            sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_customer_features_customer_id", "customer_features", ["customer_id"], unique=True)
        op.create_index("ix_customer_features_org_id", "customer_features", ["org_id"])
        op.create_index("ix_customer_features_health_score", "customer_features", ["health_score"])

    if "customer_segment_memberships" not in existing_tables:
        op.create_table(
            "customer_segment_memberships",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_segments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("org_id", sa.String(255), nullable=False),
            sa.Column("distance_to_centroid", sa.Float, nullable=True),
            sa.Column("membership_probability", sa.Float, nullable=True),
            sa.Column("previous_segment_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("customer_id", "segment_id", name="uq_customer_segment"),
        )
        op.create_index("ix_csm_customer_id", "customer_segment_memberships", ["customer_id"])
        op.create_index("ix_csm_segment_id", "customer_segment_memberships", ["segment_id"])
        op.create_index("ix_csm_org_id", "customer_segment_memberships", ["org_id"])

    if "brand_mentions" not in existing_tables:
        op.create_table(
            "brand_mentions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("org_id", sa.String(255), nullable=False),
            sa.Column("text", sa.Text, nullable=False),
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("source_url", sa.Text, nullable=True),
            sa.Column("author", sa.String(255), nullable=True),
            sa.Column("sentiment", sa.String(20), nullable=True),
            sa.Column("sentiment_score", sa.Float, nullable=True),
            sa.Column("primary_dimension", sa.String(50), nullable=True),
            sa.Column("dimension_scores", postgresql.JSONB, nullable=True),
            sa.Column("mentioned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_brand_mentions_org_id", "brand_mentions", ["org_id"])
        op.create_index("ix_brand_mentions_sentiment", "brand_mentions", ["sentiment"])
        op.create_index("ix_brand_mentions_created_at", "brand_mentions", ["created_at"])

    op.execute(sa.text("SAVEPOINT sp_ht_brand_mentions"))
    try:
        op.execute(sa.text("SELECT create_hypertable('brand_mentions', 'created_at', if_not_exists => TRUE, migrate_data => TRUE)"))
        op.execute(sa.text("RELEASE SAVEPOINT sp_ht_brand_mentions"))
    except Exception:
        op.execute(sa.text("ROLLBACK TO SAVEPOINT sp_ht_brand_mentions"))


def downgrade() -> None:
    op.drop_table("brand_mentions")
    op.drop_table("customer_segment_memberships")
    op.drop_table("customer_features")
    op.drop_table("customer_events")
    op.drop_table("orders")
