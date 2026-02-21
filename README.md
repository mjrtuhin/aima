<div align="center">

# AIMA
### Artificial Intelligence for Marketing Analytics

**Open-source, self-hosted AI marketing intelligence platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL-orange)](https://www.timescale.com/)
[![Code style: ruff](https://img.shields.io/badge/Code%20Style-ruff-000000)](https://github.com/astral-sh/ruff)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/mjrtuhin/aima/actions)

</div>

---

## What is AIMA?

AIMA is a production-ready, open-source AI platform that gives any business — from a solo Daraz seller to a mid-market e-commerce brand — access to the kind of marketing intelligence previously available only to Fortune 500 companies with $200K+/year SaaS stacks.

It unifies customer data from any source, runs seven purpose-built deep learning models continuously in the background, and surfaces decisions through a real-time dashboard and a conversational AI agent — all on your own infrastructure, with full control over your data.

**The problem it replaces:** Marketing teams today run 6–10 disconnected tools. Klaviyo for email, Segment for tracking, Northbeam for attribution, Brandwatch for social listening, Jasper for content, ChurnZero for retention — and none of them talk to each other. A customer can be about to churn while your campaign system is sending them a new customer welcome email. AIMA fixes this by making all the intelligence available in one unified system.

---

## Platform Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AIMA Platform                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   DATA SOURCES                                                      │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│   │ Shopify  │ │ Klaviyo  │ │ HubSpot  │ │ Meta Ads │ │  GA4   │  │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘  │
│        └────────────┴────────────┴────────────┴───────────┘       │
│                              │                                      │
│                   ┌──────────▼──────────┐                          │
│                   │  Google Sheet Import │  ← paste any sheet link  │
│                   │  (Auto-detect cols)  │                          │
│                   └──────────┬──────────┘                          │
│                              │                                      │
│   STORAGE LAYER              │                                      │
│   ┌───────────────┐ ┌────────▼────────┐ ┌──────────┐ ┌─────────┐  │
│   │  TimescaleDB  │ │   PostgreSQL    │ │  Redis   │ │  MinIO  │  │
│   │  (time-series)│ │ (core data)     │ │(cache+q) │ │(models) │  │
│   └───────┬───────┘ └────────┬────────┘ └────┬─────┘ └────┬────┘  │
│           └─────────────────┴───────────────┘            │        │
│                              │                                      │
│   AI PROCESSING LAYER        │                                      │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │   Celery Workers  (6 scheduled background jobs)           │    │
│   │                                                           │    │
│   │  M1: Customer    M2: Campaign   M3: Content   M4: Brand  │    │
│   │  Intelligence    Predictor      Studio        Monitor    │    │
│   │  (TBT+HDBSCAN)   (MultiTask)    (BrandVoice)  (ABSA)     │    │
│   │                                                           │    │
│   │  M5: Attribution  M6: CLV/Churn   M7: AI Agent           │    │
│   │  (Neural MMM)     (DeepHit)       (LangGraph)            │    │
│   └───────────────────────────────────────────────────────────┘    │
│                              │                                      │
│   API LAYER                  │                                      │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │    FastAPI  (12 routers, async, Pydantic v2, OpenAPI)     │    │
│   └───────────────────────────────────────────────────────────┘    │
│                              │                                      │
│   FRONTEND                   │                                      │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │    Next.js 14 · TypeScript · Tailwind · React Query       │    │
│   │    9 Pages: Dashboard | Customers | Import | Campaigns    │    │
│   │    Content Studio | Brand Monitor | Attribution           │    │
│   │    CLV & Churn | AI Agent                                 │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Desktop and Docker Compose
- Git

That is everything. The platform runs entirely inside Docker containers.

### 1. Clone and boot

```bash
git clone https://github.com/mjrtuhin/aima.git
cd aima
cp .env.example .env
docker compose up -d
```

All 13 services start automatically. First boot takes 3–5 minutes for images to download.

### 2. Open the dashboard

Navigate to **http://localhost:3000** in your browser. The dashboard is live immediately.

### 3. Import your first data

The fastest way to get started is by importing a Google Sheet. Go to **http://localhost:3000/import**, paste your sheet link, and your customers and orders are in the database in under 30 seconds.

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:3000 | Main frontend |
| REST API | http://localhost:8000 | Backend API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API docs |
| MLflow | http://localhost:5001 | Experiment tracking |
| MinIO Console | http://localhost:9001 | Object storage (user: `minio`, pass: `minio_password`) |
| Grafana | http://localhost:3001 | Metrics dashboards |
| Prometheus | http://localhost:9090 | Raw metrics |
| Flower | http://localhost:5555 | Celery task monitor |

---

## Getting Data Into AIMA

AIMA supports three ways to bring in your customer and order data, each suited to a different use case.

---

### Method 1 — Google Sheet Import (Fastest, No Code)

This is the easiest way to get started. Export your order data from any platform — Daraz, Shopify, WooCommerce, Amazon Seller Central, or a custom spreadsheet — and share it as a Google Sheet.

**Step 1 — Prepare your sheet**

Your sheet needs at minimum a header row with columns like: `Email`, `Name`, `Order Date`, `Amount`. AIMA auto-detects 14 field types — it does not care what your columns are named as long as the purpose is recognizable. A column called `Grand Total`, `GMV`, `order_amount`, or `Total` will all be detected as the order amount automatically.

Detected field types: `email`, `full_name`, `first_name`, `last_name`, `phone`, `city`, `country`, `order_id`, `order_date`, `amount`, `product_name`, `status`, `quantity`, `currency`.

**Step 2 — Share the sheet**

In Google Sheets: click **Share** → **Change to anyone with the link** → set to **Viewer** → copy the link.

**Step 3 — Import**

Go to **http://localhost:3000/import**. Paste the link. Click **Preview Columns** — AIMA will show you exactly what it detected for each column before touching your database. Then click **Import**.

**What happens next:** Your data goes directly into the `customers` and `orders` PostgreSQL tables. Go to the Segments page and click **Re-Segment** to run AI clustering over your imported buyers.

**Column detection is flexible.** Examples of what gets auto-detected:

| Your column name | Detected as |
|-----------------|-------------|
| `Buyer Email`, `Customer Email`, `mail` | `email` |
| `Grand Total`, `GMV`, `order_amount`, `sale amount` | `amount` |
| `Order Placed`, `Purchase Date`, `created_at` | `order_date` |
| `Thana`, `District`, `Zone`, `Area` | `city` |
| `Mobile`, `Contact No`, `telephone` | `phone` |

You can also run the import from the command line:

```bash
pip install psycopg2-binary --break-system-packages
python import_sheet.py "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

The CLI version shows a confirmation prompt before writing to the database and prints a full column mapping summary.

---

### Method 2 — API Connector (Automated, Real-Time Sync)

Connect AIMA directly to your live platforms. Once connected, the sync engine pulls fresh data every 30 minutes automatically.

**Connect Shopify:**

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "shopify",
    "name": "My Shopify Store",
    "credentials": {
      "shop_domain": "your-store.myshopify.com",
      "access_token": "shpat_xxxxxxxxxxxx"
    }
  }'
```

**Connect HubSpot:**

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "hubspot",
    "name": "HubSpot CRM",
    "credentials": {
      "api_key": "your-hubspot-private-app-token"
    }
  }'
```

**Connect Klaviyo:**

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "klaviyo",
    "name": "Klaviyo Email",
    "credentials": {
      "api_key": "your-klaviyo-private-key"
    }
  }'
```

**Connect Meta Ads:**

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "meta_ads",
    "name": "Facebook/Instagram Ads",
    "credentials": {
      "access_token": "your-meta-access-token",
      "ad_account_id": "act_xxxxxxxxxxxxxxx"
    }
  }'
```

**Connect Google Analytics 4:**

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "google_analytics",
    "name": "GA4 Property",
    "credentials": {
      "property_id": "123456789",
      "service_account_json": "{ ...your GA4 service account JSON... }"
    }
  }'
```

Each connector implements `validate_credentials`, `fetch_customers`, `fetch_orders`, and `fetch_events` through a shared `BaseConnector` interface, making it straightforward to add custom connectors for any platform.

---

### Method 3 — Direct Database Upsert (Advanced)

For ETL pipelines or bulk historical imports, write directly to the PostgreSQL instance at `localhost:5432` (database: `aima`, user: `aima`, password: `aima_password`). The schema is documented in the Database Schema section below.

---

## Platform Workflow

Understanding how data moves through AIMA end-to-end:

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: DATA IN                                                │
│  Google Sheet import → OR → Connector sync (every 30 min)      │
│  → Customers + Orders written to PostgreSQL                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: FEATURE ENGINEERING  (every 6 hours)                   │
│  For each customer, compute 45+ behavioral features:            │
│  Recency, Frequency, Monetary, AOV, purchase velocity,          │
│  channel diversity, product category entropy,                   │
│  inter-purchase time, LTV trajectory, engagement score          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: AI INFERENCE  (triggered on demand or scheduled)       │
│                                                                 │
│  M1 → Segment customers into behavioral personas                │
│  M2 → Predict campaign outcomes before launching                │
│  M3 → Generate personalized email/SMS content                   │
│  M4 → Score brand sentiment across 10 dimensions                │
│  M5 → Attribute revenue to each marketing channel               │
│  M6 → Predict 30/60/90-day churn risk per customer              │
│  M7 → Orchestrate all of the above via natural language         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: DECISIONS + ACTIONS                                    │
│  View insights in dashboard → Build campaigns → Generate        │
│  content → Set alert thresholds → Ask the AI agent to           │
│  build a full marketing plan with prioritized next steps        │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Seven AI Modules

---

### Module 1 — Customer Intelligence Engine

**What it does:** Automatically groups your customers into behavioral personas without you defining the segments manually. Instead of generic RFM buckets, it learns each customer's behavioral fingerprint from their full purchase and engagement history and clusters them into named personas: Champions, Loyal, At Risk, Hibernating, New Customers, Potential Loyalists, and Lost.

**The technique:** A **Temporal Behavioral Transformer (TBT)** treats each customer's event sequence as a language — tokens are purchase events, timestamps become positional encodings. A CLS token pools the entire sequence into a 128-dimensional behavioral fingerprint vector. UMAP reduces these to 2D, HDBSCAN finds natural density clusters, and a persona naming engine maps each cluster to a standard lifecycle stage using 11 rule conditions.

**Real-time drift detection:** A sliding window monitor tracks each customer's persona vector. When it crosses a threshold toward a new segment (e.g., a Champion starting to disengage), an alert fires before the customer actually churns.

**Dashboard page:** `/customers` and `/segments`

**API endpoint:** `POST /api/v1/segments/trigger`

---

### Module 2 — Campaign Performance Predictor

**What it does:** Before you send a campaign, AIMA predicts its open rate, click rate, conversion rate, expected revenue, and ROI. You can test 10 subject line variations and see predicted performance for each before spending a single dollar.

**The technique:** A **multi-task deep learning model** with two parallel encoders. A BERT-based `TextEncoder` processes the campaign subject line and body copy. A `StructuredEncoder` handles channel type, target segment, send time, audience size, and historical rates. Cross-attention fusion creates a `CampaignDNA` vector — a single representation of the campaign — which feeds five simultaneous prediction heads.

**Why multi-task matters:** Training all five outcomes jointly forces the model to learn shared representations. Understanding that high-urgency subject lines increase opens but reduce clicks, for example, is a pattern that improves all five predictions simultaneously.

**Dashboard page:** `/campaigns`

**API endpoint:** `POST /api/v1/campaigns`

---

### Module 3 — AI Content Studio

**What it does:** Generates email and SMS content that is tailored to your brand's voice and adapted to the behavioral fingerprint of the target customer segment. A campaign aimed at At-Risk customers reads differently from one aimed at Champions, even for the same product.

**The technique:** A `BrandVoiceEncoder` analyzes your existing content library and distills it into four learned scalars: formality (0–1), warmth (0–1), urgency (0–1), and complexity (0–1). These form a brand voice profile vector. The `EmailGenerator` conditions its generation on three inputs simultaneously: the brand voice profile, the target segment's behavioral fingerprint from Module 1, and the campaign objective. The output is a complete, ready-to-send email including subject line, preview text, body, CTA button text, and an HTML template.

**Dashboard page:** `/content-studio`

**API endpoints:** `POST /api/v1/content/generate/email`, `POST /api/v1/content/generate/sms`

---

### Module 4 — Brand Intelligence Monitor

**What it does:** Monitors all brand mentions across reviews, social, and forums and scores sentiment independently across ten brand dimensions: Quality, Value, Service, Delivery, Packaging, Website UX, Returns, Communication, Sustainability, and Innovation.

Standard sentiment tools tell you "this review is negative." AIMA tells you "this review is positive about Quality but negative about Delivery and neutral on Service" — so you know exactly where to focus operational improvements.

**The technique:** A `DeBERTa-v3` model fine-tuned for Aspect-Based Sentiment Analysis (ABSA). For each mention, it outputs a sentiment score in [-1, +1] for all ten dimensions simultaneously. A statistical shift detector monitors moving averages and fires alerts when any dimension declines by more than one standard deviation over a rolling window.

**Dashboard page:** `/brand-monitor`

**API endpoints:** `GET /api/v1/brand/sentiment/summary`, `GET /api/v1/brand/mentions`

---

### Module 5 — Marketing Attribution Engine

**What it does:** Answers the question: "Of all the revenue we made last month, how much was actually caused by each marketing channel?" Then recommends how to reallocate your budget to increase total revenue given the same spend.

**Why this is hard:** Last-click attribution (used by 80% of companies) gives 100% of credit to whichever touchpoint came right before a purchase. It systematically over-credits retargeting ads and under-credits awareness campaigns. If a customer saw your Instagram ad on day 1, clicked a Google ad on day 5, and bought after an email on day 7, last-click gives 100% to the email. AIMA gives credit proportionally based on causal contribution.

**The technique:** A **Neural Marketing Mix Model (Neural MMM)**. Each channel has a learned `AdstockTransform` (modeling how advertising effects decay over time — a TV ad has a longer carryover than a retargeting click) and a `SaturationTransform` (Hill function modeling diminishing returns — doubling ad spend does not double revenue). A channel interaction network captures cross-channel synergies. Revenue attribution is computed via perturbation analysis: hold all other channels constant, remove one channel's spend, and the drop in predicted revenue is that channel's true contribution.

**Budget optimizer:** Given your total budget, it computes the allocation across channels that maximizes predicted revenue under each channel's current saturation curve.

**Dashboard page:** `/attribution`

**API endpoints:** `GET /api/v1/attribution/mmm/results`, `GET /api/v1/attribution/channel-performance`, `GET /api/v1/attribution/budget-optimizer`

---

### Module 6 — CLV and Churn Intelligence Hub

**What it does:** For each customer, predicts the probability they will churn (stop buying) at 30, 60, and 90 days. Estimates each customer's remaining lifetime value. Maps risk levels to specific intervention strategies automatically.

**The technique:** A **DeepHit-inspired discrete-time survival analysis model**. Rather than outputting a single "will churn: yes/no," it outputs the full survival curve: P(active at t=30), P(active at t=60), P(active at t=90), ... This is far more useful for intervention timing — you can see not just that a customer is at risk, but when they are likely to go inactive.

Intervention mapping: Very High Risk → immediate win-back offer with discount; High Risk → personalized re-engagement campaign; Medium Risk → loyalty reward to reinforce habit; Low Risk → standard nurture sequence.

**Dashboard page:** `/clv-churn`

**API endpoints:** `GET /api/v1/clv-churn/predictions`, `GET /api/v1/clv-churn/segments`

---

### Module 7 — Autonomous AI Marketing Agent

**What it does:** A conversational AI that can query all six other modules, synthesize a complete marketing plan, and recommend a prioritized action schedule — all from a single natural-language instruction.

Example: Type "My Champions segment is growing but my At-Risk segment grew by 15% this week. What should I do?" — the agent queries Module 1 for segment data, Module 6 for churn probabilities, Module 3 to draft win-back campaign content, and returns a full prioritized plan with drafts, timelines, and expected outcomes.

**The technique:** A **LangGraph multi-agent system** with a PlannerAgent as the orchestrator. Tools registered to the agent give it access to all six module APIs. It maintains full conversation history and context across turns, understands segment-specific intervention logic (Champions → loyalty, At-Risk → win-back, New → nurture), and can generate a complete campaign schedule with subject lines, send times, audience filters, and revenue projections.

**Dashboard page:** `/agent`

**API endpoints:** `POST /api/v1/agent/chat`, `GET /api/v1/agent/history`

---

## Frontend Pages

| Page | Route | What You See |
|------|-------|--------------|
| Dashboard | `/` | System health, active segment counts, recent alerts, connector status |
| Customers | `/customers` | Full customer list with search, health scores, segment tags |
| Import Data | `/import` | Google Sheet import with column preview and detection |
| Campaigns | `/campaigns` | Campaign list, performance metrics, create campaign form |
| Content Studio | `/content-studio` | Generate email/SMS content by segment with tone and channel controls |
| Brand Monitor | `/brand-monitor` | Sentiment scores across 10 dimensions, recent mention feed |
| Attribution | `/attribution` | Channel contribution breakdown, MMM results, budget optimizer |
| CLV & Churn | `/clv-churn` | Churn probability distribution, CLV by segment, intervention recommendations |
| AI Agent | `/agent` | Chat interface — ask anything about your marketing data |

---

## API Reference

Full interactive documentation is available at **http://localhost:8000/docs** once the stack is running. Key endpoints:

### Data Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/import/preview` | Preview Google Sheet column detection without importing |
| POST | `/api/v1/import/google-sheet` | Import customers + orders from a public Google Sheet |

### Connectors

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/connectors` | Register a new data connector |
| GET | `/api/v1/connectors` | List all connectors for an org |
| DELETE | `/api/v1/connectors/{id}` | Remove a connector |

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/customers` | List customers with search, pagination |
| GET | `/api/v1/customers/{id}` | Get single customer profile |

### Segments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/segments` | List all AI-generated segments |
| POST | `/api/v1/segments/trigger` | Trigger a segmentation run |

### Campaigns

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create a new campaign |

### Content Studio

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/content/generate/email` | Generate email content for a segment |
| POST | `/api/v1/content/generate/sms` | Generate SMS content for a segment |

### Brand Monitor

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/brand/sentiment/summary` | 10-dimension sentiment scores + trend |
| GET | `/api/v1/brand/mentions` | Recent brand mentions with ABSA scores |

### Attribution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/attribution/mmm/results` | Neural MMM channel contribution results |
| GET | `/api/v1/attribution/channel-performance` | Per-channel ROI and revenue |
| GET | `/api/v1/attribution/budget-optimizer` | Budget reallocation recommendations |

### CLV & Churn

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/clv-churn/predictions` | Churn probabilities per customer |
| GET | `/api/v1/clv-churn/segments` | CLV aggregated by segment |

### AI Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agent/chat` | Send a message to the AI marketing agent |
| GET | `/api/v1/agent/history` | Conversation history |

---

## Background Processing

Six Celery tasks run automatically on schedule. No configuration required.

| Task | Schedule | What It Does |
|------|----------|--------------|
| `sync_all_connectors` | Every 30 min | Pulls fresh data from all connected platforms |
| `recompute_customer_features` | Every 6 hours | Computes 45+ behavioral features per customer |
| `update_churn_predictions` | Daily at 2am | Runs Module 6 DeepHit model over all customers |
| `update_brand_sentiment` | Every 15 min | Runs Module 4 ABSA over new brand mentions |
| `check_segment_drift` | Daily at 6am | Detects and alerts on segment composition shifts |
| `generate_weekly_reports` | Monday at 8am | Compiles cross-module performance summary |

Monitor task execution at **http://localhost:5555** (Flower).

---

## Database Schema

AIMA uses PostgreSQL extended with TimescaleDB for automatic time-series partitioning. Time-partitioned tables use hypertables for high-write performance on event streams.

| Table | Type | Key Columns |
|-------|------|-------------|
| `customers` | Regular | `id`, `org_id`, `email`, `first_name`, `last_name`, `phone`, `city`, `country`, `tags`, `properties` |
| `customer_features` | Regular | `customer_id`, `rfm_score`, `health_score`, 45+ computed behavioral metrics |
| `customer_segments` | Regular | `id`, `org_id`, `name`, `persona_type`, `size`, `avg_clv` |
| `customer_segment_memberships` | Regular | `customer_id`, `segment_id`, transition timestamps |
| `orders` | **Hypertable** (ordered_at) | `id`, `customer_id`, `amount`, `currency`, `status`, `items` (JSONB), `ordered_at` |
| `customer_events` | **Hypertable** (created_at) | `id`, `customer_id`, `event_type`, `channel`, `properties`, `created_at` |
| `brand_mentions` | **Hypertable** (created_at) | `id`, `org_id`, `content`, `source`, `sentiment_scores` (JSONB), `created_at` |
| `campaigns` | Regular | `id`, `org_id`, `name`, `channel`, `predicted_*`, `actual_*` metrics |
| `connectors` | Regular | `id`, `org_id`, `connector_type`, `credentials` (encrypted), `last_sync_at` |
| `alerts` | Regular | `id`, `org_id`, `alert_type`, `severity`, `message`, `resolved` |

Schema versioning is managed with Alembic. Migrations are in `migrations/versions/`.

---

## Tech Stack

### AI and Machine Learning

| Technology | Version | Purpose |
|-----------|---------|---------|
| PyTorch | 2.3 | All deep learning models (TBT, MultiTask, DeepHit, NeuralMMM) |
| HuggingFace Transformers | 4.x | DeBERTa-v3 ABSA, BERT campaign encoder |
| LangChain + LangGraph | Latest | Multi-agent orchestration for Module 7 |
| UMAP-learn | 0.5 | Dimensionality reduction for behavioral fingerprint clustering |
| HDBSCAN | 0.8 | Density-based clustering (handles arbitrary cluster shapes) |
| CausalML | Latest | Attribution and treatment effect estimation |
| PyMC | 5.x | Bayesian priors for marketing mix modeling |
| MLflow | 2.x | Experiment tracking, model registry, artifact storage |

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.111 | Async REST API (12 routers, 40+ endpoints) |
| SQLAlchemy | 2.0 | Async ORM with type-safe queries |
| Pydantic | v2 | Request/response validation and settings management |
| Alembic | Latest | Database schema version control |
| Celery | 5.x | Distributed background task queue |
| Structlog | Latest | Structured JSON logging |

### Data

| Technology | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 15 + TimescaleDB | Core relational data + time-series hypertables |
| Redis | 7 | Celery broker/backend, session cache |
| Apache Kafka | 3.x | Real-time behavioral event streaming |
| MinIO | Latest | S3-compatible object storage for models and exports |
| dbt | Core | SQL-based 3-layer transformation pipeline |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 14 (App Router) | Server-side rendering, file-based routing |
| TypeScript | Strict mode | Full type safety across all components |
| Tailwind CSS | 3.x | Utility-first styling |
| React Query | 5.x | Server state management and intelligent caching |
| Recharts | 2.x | Interactive analytics charts and visualizations |
| Lucide React | Latest | Icon system |
| Axios | Latest | HTTP client with interceptors |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker Compose | Full 13-service local stack in one command |
| Kubernetes + Helm | Production autoscaling and rolling deployments |
| GitHub Actions | CI/CD: lint → test → build → deploy |
| Prometheus | API metrics, ML inference latency, business KPIs |
| Grafana | Auto-provisioned dashboards for all metrics |

---

## Repository Structure

```
aima/
├── modules/                     # Seven AI modules
│   ├── customer_intelligence/   # M1: TBT + UMAP/HDBSCAN
│   │   ├── models/              #   TemporalBehavioralTransformer
│   │   ├── features/            #   FeatureEngineer (45+ features)
│   │   ├── clustering/          #   DynamicClusteringEngine + DriftDetector
│   │   └── api/                 #   FastAPI router
│   ├── campaign_predictor/      # M2: MultiTaskPerformancePredictor
│   ├── content_studio/          # M3: BrandVoiceEncoder + EmailGenerator
│   ├── brand_monitor/           # M4: ABSAModel (DeBERTa, 10 dimensions)
│   ├── attribution/             # M5: NeuralMMMModel (adstock + saturation)
│   ├── clv_churn/               # M6: DeepChurnModel (survival analysis)
│   └── agent/                   # M7: PlannerAgent (LangGraph)
│
├── platform/                    # Backend infrastructure
│   ├── api/                     # FastAPI app, models, config
│   │   ├── routers/             #   12 route handlers
│   │   ├── models.py            #   SQLAlchemy ORM models
│   │   ├── database.py          #   Async engine + session factory
│   │   └── main.py              #   App factory and middleware
│   └── workers/                 # Celery tasks (sync, inference, reporting)
│
├── data/                        # Data layer
│   ├── connectors/              # Shopify, Klaviyo, HubSpot, Meta Ads, GA4
│   ├── pipelines/               # dbt project (staging + mart models)
│   └── schemas/                 # TimescaleDB init SQL with hypertables
│
├── frontend/                    # Next.js 14 dashboard
│   ├── app/                     # 9 module pages (App Router)
│   │   ├── page.tsx             #   Dashboard
│   │   ├── customers/           #   Customers list + health scores
│   │   ├── import/              #   Google Sheet import UI
│   │   ├── campaigns/           #   Campaign management
│   │   ├── content-studio/      #   AI content generation
│   │   ├── brand-monitor/       #   ABSA sentiment dashboard
│   │   ├── attribution/         #   MMM + budget optimizer
│   │   ├── clv-churn/           #   Survival analysis dashboard
│   │   └── agent/               #   AI agent chat interface
│   ├── components/              #   Sidebar, shared UI components
│   └── lib/                     #   API client (axios)
│
├── migrations/                  # Alembic versioned schema migrations
├── monitoring/                  # Prometheus config + Grafana dashboards
├── scripts/                     # Training scripts for modules 1, 2, 6
├── tests/                       # Unit tests (39 test cases)
├── k8s/                         # Kubernetes Helm values
├── import_sheet.py              # CLI Google Sheet importer
├── docker-compose.yml           # Full local stack (13 services)
├── pyproject.toml               # Python project + all dependencies
└── Makefile                     # Developer workflow commands
```

---

## Developer Workflow

```bash
make dev          # Start all Docker services
make migrate      # Run Alembic schema migrations
make test         # Run pytest with coverage report
make lint         # ruff check + mypy type checking
make format       # Auto-format with ruff
make train-all    # Download data, prepare sequences, train modules 1/2/6
make dbt-run      # Run dbt transformation pipeline
make dbt-test     # Run dbt data quality tests
make clean        # Remove caches and compiled files
```

---

## Adding a Custom Connector

Adding a new data source connector requires implementing one class with four methods. AIMA handles registration, scheduling, and error handling automatically.

```python
from data.connectors.base import BaseConnector, ConnectorRegistry

@ConnectorRegistry.register("my_platform")
class MyPlatformConnector(BaseConnector):

    def validate_credentials(self) -> bool:
        ...

    def fetch_customers(self, since: datetime) -> list[CustomerRecord]:
        ...

    def fetch_orders(self, since: datetime) -> list[OrderRecord]:
        ...

    def fetch_events(self, since: datetime) -> list[EventRecord]:
        ...
```

No other changes are required. The connector self-registers with the registry and becomes available immediately through `POST /api/v1/connectors` with `"connector_type": "my_platform"`.

---

## Research Contributions

AIMA is designed as both a production platform and a research vehicle. Seven peer-reviewed papers are planned from this codebase:

| Paper | Target Venue | Core Contribution |
|-------|-------------|-------------------|
| *Dynamic Customer Persona Generation via Temporal Behavioral Transformers* | KDD 2026 | Novel TBT architecture for behavioral fingerprinting |
| *Pre-Launch Campaign Performance Prediction via Multi-Modal Encoding* | WWW 2026 | Multi-task campaign outcome prediction before send |
| *Conversion-Optimized Content Generation via Outcome-Supervised LLM Fine-Tuning* | ACL 2026 | Brand-voice-conditioned marketing copy generation |
| *Temporal Brand Perception Modeling via Aspect-Level Sentiment Analysis* | Journal of Marketing Research | 10-dimension ABSA for brand intelligence |
| *Unified Causal Attribution: MMM and MTA Reconciliation via Neural Adstock Models* | Marketing Science | Neural MMM with learnable per-channel adstock and saturation |
| *Causal CLV Optimization via Individual Treatment Effect Estimation* | KDD / JMR | Survival analysis for churn prediction and CLV |
| *Towards Autonomous Marketing: Multi-Agent LLM Framework and AIMA-Bench* | AAAI / NeurIPS | Multi-agent AI orchestration and benchmark for marketing AI |

---

## Testing and CI/CD

```bash
make test
```

The test suite covers the three most architecturally complex subsystems:

- `tests/unit/test_feature_engineer.py` — 15 tests for RFM computation, health score calculation, temporal feature extraction, and feature vector serialization
- `tests/unit/test_clustering.py` — 11 tests for segment persona naming rules, UMAP+HDBSCAN pipeline, and drift detection logic
- `tests/unit/test_connectors.py` — 13 tests for the BaseConnector interface, registry decorator pattern, and data record dataclasses

GitHub Actions runs the full pipeline on every push: lint with `ruff` and `mypy`, tests with PostgreSQL and Redis service containers, multi-stage Docker build, and deployment to Kubernetes on merge to main.

---

## Contributing

Contributions are welcome across all areas — new AI models, new data connectors, frontend improvements, research experiments, and documentation.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, branch naming, and pull request guidelines.

---

## License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## Author

<div align="center">

### Md Julfikar Rahman Tuhin

**AI/ML Engineer · Full-Stack Developer · Marketing Technology Researcher**

</div>

AIMA is designed, architected, and built by Md Julfikar Rahman Tuhin — an AI/ML engineer with deep expertise across the full stack of modern machine learning systems, from research-grade model architecture to production infrastructure.

**Technical depth behind this project:**

The platform reflects hands-on experience across multiple domains that rarely intersect in a single engineer:

- **Deep learning architecture** — Transformer-based sequence models (TBT), multi-task learning with cross-attention fusion (Campaign Predictor), discrete-time survival analysis (DeepHit CLV/Churn), and learnable causal inference models (Neural MMM with adstock and saturation transforms)
- **NLP and LLMs** — ABSA fine-tuning on DeBERTa-v3, brand voice embedding, LLM-conditioned content generation, and multi-agent orchestration via LangGraph
- **Production ML systems** — MLflow experiment tracking, Celery-based async inference workers, feature engineering pipelines, model artifact management with MinIO, and full observability via Prometheus and Grafana
- **Backend engineering** — Async FastAPI at scale, SQLAlchemy 2.0 async ORM, TimescaleDB hypertables for high-write time-series workloads, Alembic schema migrations, Redis-backed Celery queuing across four named queues
- **Data engineering** — Apache Kafka event streaming, dbt 3-layer transformation pipeline (raw → staging → marts), five production API connectors (Shopify, Klaviyo, HubSpot, Meta Ads, GA4)
- **Frontend engineering** — Next.js 14 App Router with TypeScript strict mode, React Query server state management, Recharts and D3.js visualizations, and a full design system in Tailwind CSS
- **Infrastructure** — Full Docker Compose local development stack (13 services), Kubernetes Helm charts for production, GitHub Actions CI/CD pipeline, and auto-provisioned Grafana dashboards

**The motivation behind AIMA:**

The fragmentation of marketing technology has created a perverse situation where mid-market businesses — the ones who need intelligence the most — are priced out of enterprise tools, left to make million-dollar campaign decisions based on spreadsheet intuition. The 2025 marketing SaaS landscape charges $30,000–$200,000 per year for tools that should be commodity infrastructure.

AIMA is a statement that this does not have to be true. Every technique in this platform — behavioral transformers, survival analysis, neural marketing mix models, multi-agent orchestration — is built on public research. The gap has never been the science. It has been the engineering and the packaging.

This project is both a platform and a research contribution. The goal is to publish the architectural and empirical findings from each module as peer-reviewed papers targeting KDD, WWW, ACL, NeurIPS, and Marketing Science — establishing a rigorous, reproducible foundation for AI-native marketing intelligence.

---

<div align="center">

Built with precision. Open-sourced with purpose.

**[GitHub](https://github.com/mjrtuhin/aima)** · MIT License

</div>
