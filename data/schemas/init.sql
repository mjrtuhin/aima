CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'pgvector extension not available, skipping (install pgvector for vector similarity search)';
END
$$;

CREATE DATABASE mlflow;

CREATE TYPE connector_type AS ENUM (
    'shopify', 'woocommerce', 'magento', 'bigcommerce',
    'hubspot', 'salesforce', 'pipedrive', 'zoho',
    'klaviyo', 'mailchimp', 'activecampaign', 'brevo',
    'meta_ads', 'google_ads', 'tiktok_ads', 'linkedin_ads',
    'ga4', 'mixpanel', 'amplitude',
    'twitter', 'instagram', 'facebook', 'linkedin', 'youtube',
    'csv', 'json', 'postgresql', 'mysql', 'bigquery', 'snowflake'
);

CREATE TYPE campaign_channel AS ENUM (
    'email', 'sms', 'push', 'meta_ads', 'google_ads',
    'tiktok_ads', 'linkedin_ads', 'twitter_ads', 'display'
);

CREATE TYPE campaign_status AS ENUM (
    'draft', 'scheduled', 'running', 'paused', 'completed', 'cancelled'
);

CREATE TYPE segment_status AS ENUM ('active', 'archived', 'stale');

CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE connectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type connector_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    credentials_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    last_synced_at TIMESTAMPTZ,
    sync_frequency_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (org_id, type, name)
);

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    connector_id UUID REFERENCES connectors(id),
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    timezone VARCHAR(50),
    tags TEXT[],
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (org_id, external_id, connector_id)
);

CREATE TABLE customer_events (
    id UUID DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    source VARCHAR(100),
    occurred_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('customer_events', 'occurred_at', if_not_exists => TRUE);
CREATE INDEX ON customer_events (org_id, customer_id, occurred_at DESC);
CREATE INDEX ON customer_events (org_id, event_type, occurred_at DESC);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    connector_id UUID REFERENCES connectors(id),
    external_id VARCHAR(255),
    order_number VARCHAR(100),
    status VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    subtotal NUMERIC(12, 2),
    total NUMERIC(12, 2),
    discount_total NUMERIC(12, 2) DEFAULT 0,
    tax_total NUMERIC(12, 2) DEFAULT 0,
    items JSONB DEFAULT '[]',
    channel VARCHAR(100),
    properties JSONB DEFAULT '{}',
    ordered_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('orders', 'ordered_at', if_not_exists => TRUE);
CREATE INDEX ON orders (org_id, customer_id, ordered_at DESC);
CREATE INDEX ON orders (org_id, ordered_at DESC);

CREATE TABLE customer_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    feature_version INTEGER NOT NULL DEFAULT 1,
    recency_days INTEGER,
    frequency INTEGER,
    monetary_value NUMERIC(12, 2),
    avg_order_value NUMERIC(12, 2),
    max_order_value NUMERIC(12, 2),
    min_order_value NUMERIC(12, 2),
    order_value_std NUMERIC(12, 2),
    total_items_purchased INTEGER,
    avg_items_per_order NUMERIC(8, 2),
    unique_products_count INTEGER,
    unique_categories_count INTEGER,
    purchase_tenure_days INTEGER,
    avg_days_between_purchases NUMERIC(8, 2),
    purchase_acceleration NUMERIC(8, 4),
    email_open_rate NUMERIC(5, 4),
    email_click_rate NUMERIC(5, 4),
    email_conversion_rate NUMERIC(5, 4),
    cart_abandonment_rate NUMERIC(5, 4),
    website_visit_frequency NUMERIC(8, 2),
    avg_session_duration_seconds INTEGER,
    preferred_day_of_week SMALLINT,
    preferred_hour_of_day SMALLINT,
    price_sensitivity_score NUMERIC(5, 4),
    brand_loyalty_score NUMERIC(5, 4),
    new_product_adoption_rate NUMERIC(5, 4),
    customer_health_score NUMERIC(5, 2),
    behavioral_vector FLOAT[],
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (org_id, customer_id, feature_version)
);

CREATE TABLE customer_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_version VARCHAR(50),
    cluster_id INTEGER,
    customer_count INTEGER DEFAULT 0,
    avg_health_score NUMERIC(5, 2),
    avg_ltv NUMERIC(12, 2),
    characteristics JSONB DEFAULT '{}',
    recommended_strategy TEXT,
    status segment_status DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE customer_segment_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES customer_segments(id) ON DELETE CASCADE,
    confidence_score NUMERIC(5, 4),
    previous_segment_id UUID REFERENCES customer_segments(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (customer_id, segment_id)
);

CREATE TABLE churn_predictions (
    id UUID DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    churn_probability_30d NUMERIC(5, 4),
    churn_probability_90d NUMERIC(5, 4),
    predicted_ltv NUMERIC(12, 2),
    recommended_intervention VARCHAR(100),
    intervention_expected_impact JSONB,
    model_version VARCHAR(50),
    predicted_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('churn_predictions', 'predicted_at', if_not_exists => TRUE);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    channel campaign_channel NOT NULL,
    status campaign_status DEFAULT 'draft',
    target_segment_id UUID REFERENCES customer_segments(id),
    subject_line VARCHAR(500),
    preview_text VARCHAR(500),
    content JSONB DEFAULT '{}',
    offer_type VARCHAR(100),
    offer_value NUMERIC(8, 2),
    predicted_open_rate NUMERIC(5, 4),
    predicted_click_rate NUMERIC(5, 4),
    predicted_conversion_rate NUMERIC(5, 4),
    predicted_revenue NUMERIC(12, 2),
    predicted_roi NUMERIC(8, 4),
    actual_open_rate NUMERIC(5, 4),
    actual_click_rate NUMERIC(5, 4),
    actual_conversion_rate NUMERIC(5, 4),
    actual_revenue NUMERIC(12, 2),
    budget NUMERIC(12, 2),
    scheduled_at TIMESTAMPTZ,
    launched_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE campaign_metrics (
    id UUID DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15, 4),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('campaign_metrics', 'recorded_at', if_not_exists => TRUE);

CREATE TABLE brand_mentions (
    id UUID DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL,
    source_id VARCHAR(500),
    author VARCHAR(255),
    author_followers INTEGER,
    content TEXT,
    url VARCHAR(2000),
    sentiment_overall NUMERIC(5, 4),
    sentiment_product_quality NUMERIC(5, 4),
    sentiment_customer_service NUMERIC(5, 4),
    sentiment_pricing NUMERIC(5, 4),
    sentiment_brand_trust NUMERIC(5, 4),
    sentiment_innovation NUMERIC(5, 4),
    sentiment_sustainability NUMERIC(5, 4),
    sentiment_ux NUMERIC(5, 4),
    sentiment_delivery NUMERIC(5, 4),
    sentiment_brand_personality NUMERIC(5, 4),
    sentiment_competitive_position NUMERIC(5, 4),
    reach INTEGER,
    engagement INTEGER,
    is_competitor BOOLEAN DEFAULT false,
    competitor_name VARCHAR(255),
    mentioned_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('brand_mentions', 'mentioned_at', if_not_exists => TRUE);
CREATE INDEX ON brand_mentions (org_id, mentioned_at DESC);
CREATE INDEX ON brand_mentions (org_id, source, mentioned_at DESC);

CREATE TABLE attribution_touchpoints (
    id UUID DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id),
    channel campaign_channel,
    campaign_id UUID REFERENCES campaigns(id),
    touchpoint_data JSONB DEFAULT '{}',
    attribution_credit_last_click NUMERIC(5, 4),
    attribution_credit_first_click NUMERIC(5, 4),
    attribution_credit_linear NUMERIC(5, 4),
    attribution_credit_aima NUMERIC(5, 4),
    occurred_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('attribution_touchpoints', 'occurred_at', if_not_exists => TRUE);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity alert_severity DEFAULT 'medium',
    title VARCHAR(500) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON alerts (org_id, is_read, created_at DESC);

CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id),
    module VARCHAR(100) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    mlflow_run_id VARCHAR(255),
    metrics JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    artifact_path VARCHAR(1000),
    is_active BOOLEAN DEFAULT false,
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (org_id, module, model_name, model_version)
);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_connectors_updated_at
    BEFORE UPDATE ON connectors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX ON customers (org_id, email);
CREATE INDEX ON customers (org_id, created_at DESC);
CREATE INDEX ON customer_features (org_id, customer_id);
CREATE INDEX ON customer_segment_memberships (segment_id);
CREATE INDEX ON campaign_metrics (campaign_id, recorded_at DESC);
