"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    existing_enums = {e["name"] for e in inspector.get_enums()}

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    connector_type = postgresql.ENUM(
        "shopify", "woocommerce", "magento", "bigcommerce",
        "hubspot", "salesforce", "pipedrive", "zoho",
        "klaviyo", "mailchimp", "activecampaign", "brevo",
        "meta_ads", "google_ads", "tiktok_ads", "linkedin_ads",
        "ga4", "mixpanel", "amplitude",
        "twitter", "instagram", "facebook", "linkedin", "youtube",
        "csv", "json", "postgresql", "mysql", "bigquery", "snowflake",
        name="connector_type",
    )
    connector_type.create(op.get_bind(), checkfirst=True)

    campaign_channel = postgresql.ENUM(
        "email", "sms", "push", "meta_ads", "google_ads",
        "tiktok_ads", "linkedin_ads", "twitter_ads", "display",
        name="campaign_channel",
    )
    campaign_channel.create(op.get_bind(), checkfirst=True)

    campaign_status = postgresql.ENUM(
        "draft", "scheduled", "running", "paused", "completed", "cancelled",
        name="campaign_status",
    )
    campaign_status.create(op.get_bind(), checkfirst=True)

    alert_severity = postgresql.ENUM(
        "low", "medium", "high", "critical",
        name="alert_severity",
    )
    alert_severity.create(op.get_bind(), checkfirst=True)

    if "organizations" not in existing_tables:
        op.create_table(
            "organizations",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("slug", sa.String(100), nullable=False, unique=True),
            sa.Column("settings", postgresql.JSONB, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if "connectors" not in existing_tables:
        op.create_table(
            "connectors",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", postgresql.ENUM(name="connector_type", create_type=False), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("config", postgresql.JSONB, server_default="{}"),
            sa.Column("credentials_encrypted", sa.Text),
            sa.Column("is_active", sa.Boolean, server_default="true"),
            sa.Column("last_synced_at", sa.DateTime(timezone=True)),
            sa.Column("sync_frequency_minutes", sa.Integer, server_default="60"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("org_id", "type", "name", name="uq_connector_org_type_name"),
        )

    if "customers" not in existing_tables:
        op.create_table(
            "customers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("external_id", sa.String(255)),
            sa.Column("connector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connectors.id")),
            sa.Column("email", sa.String(255)),
            sa.Column("first_name", sa.String(100)),
            sa.Column("last_name", sa.String(100)),
            sa.Column("phone", sa.String(50)),
            sa.Column("country", sa.String(100)),
            sa.Column("city", sa.String(100)),
            sa.Column("timezone", sa.String(50)),
            sa.Column("tags", postgresql.ARRAY(sa.String)),
            sa.Column("properties", postgresql.JSONB, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_customers_org_email", "customers", ["org_id", "email"])
        op.create_index("ix_customers_org_created", "customers", ["org_id", "created_at"])

    if "customer_segments" not in existing_tables:
        op.create_table(
            "customer_segments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text),
            sa.Column("model_version", sa.String(50)),
            sa.Column("cluster_id", sa.Integer),
            sa.Column("customer_count", sa.Integer, server_default="0"),
            sa.Column("avg_health_score", sa.Numeric(5, 2)),
            sa.Column("avg_ltv", sa.Numeric(12, 2)),
            sa.Column("characteristics", postgresql.JSONB, server_default="{}"),
            sa.Column("recommended_strategy", sa.Text),
            sa.Column("status", sa.String(20), server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if "campaigns" not in existing_tables:
        op.create_table(
            "campaigns",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("channel", postgresql.ENUM(name="campaign_channel", create_type=False), nullable=False),
            sa.Column("status", postgresql.ENUM(name="campaign_status", create_type=False), server_default="draft"),
            sa.Column("target_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customer_segments.id")),
            sa.Column("subject_line", sa.String(500)),
            sa.Column("preview_text", sa.String(500)),
            sa.Column("content", postgresql.JSONB, server_default="{}"),
            sa.Column("offer_type", sa.String(100)),
            sa.Column("offer_value", sa.Numeric(8, 2)),
            sa.Column("predicted_open_rate", sa.Numeric(5, 4)),
            sa.Column("predicted_click_rate", sa.Numeric(5, 4)),
            sa.Column("predicted_conversion_rate", sa.Numeric(5, 4)),
            sa.Column("predicted_revenue", sa.Numeric(12, 2)),
            sa.Column("predicted_roi", sa.Numeric(8, 4)),
            sa.Column("actual_open_rate", sa.Numeric(5, 4)),
            sa.Column("actual_click_rate", sa.Numeric(5, 4)),
            sa.Column("actual_conversion_rate", sa.Numeric(5, 4)),
            sa.Column("actual_revenue", sa.Numeric(12, 2)),
            sa.Column("budget", sa.Numeric(12, 2)),
            sa.Column("scheduled_at", sa.DateTime(timezone=True)),
            sa.Column("launched_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if "alerts" not in existing_tables:
        op.create_table(
            "alerts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("alert_type", sa.String(100), nullable=False),
            sa.Column("severity", postgresql.ENUM(name="alert_severity", create_type=False), server_default="medium"),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("message", sa.Text),
            sa.Column("data", postgresql.JSONB, server_default="{}"),
            sa.Column("is_read", sa.Boolean, server_default="false"),
            sa.Column("is_resolved", sa.Boolean, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_alerts_org_read", "alerts", ["org_id", "is_read", "created_at"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("campaigns")
    op.drop_table("customer_segments")
    op.drop_table("customers")
    op.drop_table("connectors")
    op.drop_table("organizations")
