<div align="center">

# AIMA
### Artificial Intelligence for Marketing Analytics

**Open-source, end-to-end AI marketing intelligence platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Code style: ruff](https://img.shields.io/badge/Code%20Style-ruff-000000)](https://github.com/astral-sh/ruff)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/mjrtuhin/aima/actions)

</div>

---

## What is AIMA?

AIMA is a production-ready, open-source AI platform that gives any organization access to the kind of marketing intelligence previously available only to Fortune 500 companies. It unifies customer data from fragmented sources, applies seven purpose-built deep learning models, and surfaces decisions through a real-time dashboard and a multi-agent AI orchestration layer.

The platform is also a research vehicle. Every module is grounded in a novel research contribution targeting top-tier venues (KDD, WWW, ACL, NeurIPS). The codebase is written to production standards: typed Python, async FastAPI, Alembic migrations, Celery workers, Docker Compose locally, Kubernetes in production, and full CI/CD via GitHub Actions.

---

## Seven AI Modules

### Module 1 - Customer Intelligence Engine

**Problem:** Traditional RFM segmentation (invented in 1970) treats all customers the same if they share recency, frequency, and monetary values. It ignores browsing behavior, content engagement, purchase sequences, and temporal patterns.

**Solution:** A novel **Temporal Behavioral Transformer (TBT)** that treats a customer's entire history as a sequence and learns dense behavioral fingerprint vectors via contrastive self-supervised learning. These vectors are then clustered using UMAP dimensionality reduction and HDBSCAN density clustering into named personas (Champions, At Risk, Hibernating, etc.), with a drift detector that fires alerts when a customer transitions across critical boundaries.

**Key techniques:** Transformer encoder with CLS token pooling, contrastive loss, UMAP, HDBSCAN, RFM feature engineering (45+ computed features), automated segment naming via 11 persona rules, real-time drift detection.

---

### Module 2 - Campaign Performance Predictor

**Problem:** Marketers spend budgets based on intuition. There is no system that reliably forecasts open rates, click rates, conversion rates, and revenue for a campaign before it launches.

**Solution:** A **multi-task deep learning model** that jointly predicts five campaign outcomes simultaneously. It encodes campaign content via a BERT-based TextEncoder and structured metadata (channel, audience size, send time, historical rates) via a StructuredEncoder, then fuses them with cross-attention to form a CampaignDNA representation, which feeds five specialized prediction heads.

**Key techniques:** Multi-modal encoding, cross-attention fusion, multi-task learning with shared representations, five simultaneous regression heads (open rate, click rate, conversion rate, revenue, ROI).

---

### Module 3 - AI Content Studio

**Problem:** Generic AI writing tools produce correct text but do not know your brand voice, your audience's response patterns, or the optimal content structure for your specific customer segments.

**Solution:** A **BrandVoiceEncoder** that learns four brand personality dimensions (formality, warmth, urgency, complexity) from a brand's existing content library. An EmailGenerator then conditions content generation on the brand voice profile, the target segment's behavioral fingerprint, and the campaign objective, producing subject line variants, preview text, body copy, CTA, and a complete HTML template.

**Key techniques:** Brand voice embedding from content samples, segment-conditioned generation, LLM backend with template fallback, multi-channel support (email, SMS, push, WhatsApp).

---

### Module 4 - Brand Intelligence Monitor

**Problem:** Social listening tools count mentions and classify them as positive or negative. They cannot tell you whether complaints are about delivery speed, product quality, customer service, or your website. You cannot fix what you cannot measure at dimension level.

**Solution:** An **Aspect-Based Sentiment Analysis (ABSA)** model built on DeBERTa-v3 that scores sentiment independently across ten brand dimensions: Quality, Value, Service, Delivery, Packaging, Website UX, Returns, Communication, Sustainability, and Innovation. The system monitors real-time brand mentions, tracks dimension-level trends over time, and fires alerts when any dimension shows a statistically significant negative shift.

**Key techniques:** DeBERTa-v3 fine-tuned for ABSA, ten-dimension sentiment scoring, keyword-based fallback, time-series trend analysis, alert threshold detection.

---

### Module 5 - Marketing Attribution Engine

**Problem:** Last-click attribution, used by 80% of companies, gives 100% of purchase credit to the final touchpoint. This causes systematic over-investment in bottom-funnel channels and under-investment in awareness. Billions of dollars are misallocated annually because of this.

**Solution:** A **Neural Marketing Mix Model (Neural MMM)** that learns the true causal contribution of each marketing channel to revenue. Each channel has a learned AdstockTransform (modeling the carryover effect of advertising) and a SaturationTransform (Hill function modeling diminishing returns). A channel interaction network captures cross-channel synergies. Channel ROI is computed via perturbation analysis, and a budget optimizer recommends reallocation to maximize expected revenue.

**Key techniques:** Learnable adstock decay per channel, Hill function saturation curves, channel interaction modeling, perturbation-based ROI attribution, budget optimization under saturation constraints.

---

### Module 6 - CLV and Churn Intelligence Hub

**Problem:** Most companies discover churn 6 months after it happens. The behavioral signals (declining email engagement, reduced browsing, lower order values) were visible months earlier, but no system was watching.

**Solution:** A **DeepHit-inspired survival analysis model** that outputs the full survival curve for each customer: the probability of remaining active at each future time step. This gives 30, 60, and 90-day churn probabilities plus a predicted Customer Lifetime Value. The model maps each risk level to a specific intervention (immediate win-back offer, personalized discount, engagement campaign, loyalty reward) and flags at-risk segments before they deteriorate.

**Key techniques:** Discrete-time survival analysis, cause-specific hazard modeling, survival curve estimation, individual-level intervention recommendation, segment-level CLV aggregation.

---

### Module 7 - Autonomous AI Marketing Agent

**Problem:** All the intelligence from modules 1-6 is worthless if it sits in dashboards that nobody acts on. Marketing teams are overwhelmed and cannot systematically act on every insight.

**Solution:** A **multi-agent AI orchestration system** built on LangGraph that can receive natural-language instructions, query modules 1-6 for current data, synthesize a marketing plan, and generate a prioritized campaign schedule. The planner agent understands segment context (e.g., it knows that At-Risk customers need win-back campaigns, that Champions should receive loyalty rewards, and that New Customers need nurture sequences). Users interact through a chat interface.

**Key techniques:** LangGraph multi-agent orchestration, tool use across all 6 other modules, rule-based plan generation with LLM enhancement, segment-aware campaign design, full conversation history management.

---

## Architecture

```
                           AIMA Platform
  ───────────────────────────────────────────────────────────

  Frontend (Next.js 14 + TypeScript + Tailwind + Recharts)
       Dashboard | Segments | Campaigns | Content Studio
       Brand Monitor | Attribution | CLV/Churn | AI Agent

  ───────────────────────────────────────────────────────────

  REST API (FastAPI + async SQLAlchemy + Pydantic v2)
       11 Routers | JWT Auth | Prometheus Metrics | OpenAPI

  ───────────────────────────────────────────────────────────

  AI Modules (PyTorch + HuggingFace + LangGraph)
    M1: Temporal       M2: Multi-Task     M3: Brand Voice
    Behavioral         Campaign           Encoder +
    Transformer +      Predictor          Email Generator
    UMAP/HDBSCAN

    M4: DeBERTa        M5: Neural MMM     M6: DeepHit
    ABSA (10           Adstock +          Survival
    dimensions)        Saturation         Analysis

                    M7: LangGraph
                    Multi-Agent Planner

  ───────────────────────────────────────────────────────────

  Background Workers (Celery + Redis)
    Sync (*/30min) | Features (*/6h) | Churn (2am daily)
    Sentiment (*/15min) | Drift (6am) | Reports (Mon 8am)

  ───────────────────────────────────────────────────────────

  Data Layer
    TimescaleDB     Redis          Apache Kafka
    (time-series    (cache +       (event streaming)
    hypertables)    queue)

    MinIO           MLflow         dbt
    (model          (experiment    (SQL
    artifacts)      tracking)      transforms)

  ───────────────────────────────────────────────────────────

  Data Connectors
    Shopify   Klaviyo   HubSpot   Meta Ads   GA4   ...

  ───────────────────────────────────────────────────────────

  Infrastructure
    Docker Compose (local) | Kubernetes + Helm (production)
    GitHub Actions CI/CD | Prometheus + Grafana monitoring
```

---

## Tech Stack

### AI and Machine Learning

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Deep Learning | PyTorch 2.3 | Transformer, survival analysis, MMM models |
| Language Models | HuggingFace Transformers | DeBERTa ABSA, BERT campaign encoder |
| LLM Orchestration | LangChain + LangGraph | Multi-agent marketing planner |
| Clustering | UMAP + HDBSCAN | Behavioral fingerprint clustering |
| Causal Inference | CausalML | Attribution and treatment effects |
| Bayesian Modeling | PyMC | Marketing mix modeling priors |
| Experiment Tracking | MLflow | Hyperparameter logging, model registry |

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI (async) | High-performance REST API |
| ORM | SQLAlchemy 2.0 (async) | Type-safe async database access |
| Validation | Pydantic v2 | Request/response validation and settings |
| Migrations | Alembic | Schema version control |
| Task Queue | Celery + Redis | Background ML inference and sync jobs |
| Logging | Structlog | Structured JSON logging |

### Data

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Primary Database | PostgreSQL + TimescaleDB | Relational data + time-series hypertables |
| Cache and Queue | Redis | Session cache, Celery broker/backend |
| Event Streaming | Apache Kafka | Real-time behavioral event ingestion |
| Object Storage | MinIO | Model artifacts, data exports |
| Transformations | dbt | SQL-based 3-layer transformation pipeline |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 14 (App Router) | Server-side rendering and routing |
| Language | TypeScript (strict mode) | Full type safety |
| Styling | Tailwind CSS | Utility-first styling |
| Data Fetching | React Query | Server state management and caching |
| Charts | Recharts + D3.js | Interactive analytics visualizations |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Local Dev | Docker Compose | Full 10-service local stack in one command |
| Production | Kubernetes + Helm | Autoscaling, rolling deployments |
| CI/CD | GitHub Actions | Lint, test, build, deploy pipeline |
| Monitoring | Prometheus + Grafana | API metrics, ML inference latency, business KPIs |

---

## Repository Structure

```
aima/
├── modules/                    # Seven AI modules
│   ├── customer_intelligence/  # Module 1: TBT + UMAP/HDBSCAN clustering
│   │   ├── models/             #   TemporalBehavioralTransformer
│   │   ├── features/           #   FeatureEngineer (45+ features)
│   │   ├── clustering/         #   DynamicClusteringEngine + DriftDetector
│   │   └── api/                #   FastAPI router
│   ├── campaign_predictor/     # Module 2: MultiTaskPerformancePredictor
│   ├── content_studio/         # Module 3: BrandVoiceEncoder + EmailGenerator
│   ├── brand_monitor/          # Module 4: ABSAModel (DeBERTa, 10 dimensions)
│   ├── attribution/            # Module 5: NeuralMMMModel (adstock + saturation)
│   ├── clv_churn/              # Module 6: DeepChurnModel (survival analysis)
│   └── agent/                  # Module 7: PlannerAgent (LangGraph)
│
├── platform/                   # Backend infrastructure
│   ├── api/                    # FastAPI app, models, config, 11 routers
│   └── workers/                # Celery tasks (sync, inference, reporting)
│
├── data/                       # Data layer
│   ├── connectors/             # Shopify, Klaviyo, HubSpot, Meta Ads, GA4
│   ├── pipelines/              # dbt project (staging + mart models)
│   └── schemas/                # TimescaleDB init SQL with hypertables
│
├── frontend/                   # Next.js 14 dashboard
│   ├── app/                    # 8 module pages (App Router)
│   └── components/             # Shared UI components
│
├── migrations/                 # Alembic migrations (versioned schema)
├── monitoring/                 # Prometheus config + Grafana dashboards
├── scripts/                    # Training scripts for modules 1, 2, 6
├── tests/                      # Unit tests (30 test cases)
├── k8s/                        # Kubernetes Helm values
├── docker-compose.yml          # Full local stack (10 services)
├── pyproject.toml              # Python project + all dependencies
└── Makefile                    # Developer workflow commands
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend development)

### Run the full stack locally

```bash
git clone https://github.com/mjrtuhin/aima.git
cd aima
cp .env.example .env
docker compose up -d
```

This starts 10 services: TimescaleDB, Redis, Kafka, MinIO, MLflow, FastAPI, Celery Worker, Celery Beat, Next.js, and Prometheus.

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| REST API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| MLflow Tracking | http://localhost:5000 |
| MinIO Console | http://localhost:9001 |
| Grafana | http://localhost:3001 |

### Run database migrations

```bash
make migrate
```

### Connect your first data source

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "my-org",
    "connector_type": "shopify",
    "name": "My Shopify Store",
    "credentials": {
      "shop_domain": "your-store.myshopify.com",
      "access_token": "your-token"
    }
  }'
```

### Run customer segmentation

```bash
curl -X POST http://localhost:8000/api/v1/modules/customer-intelligence/segment \
  -H "Content-Type: application/json" \
  -d '{"org_id": "my-org", "connector_id": "shopify-1", "n_segments": "auto"}'
```

### Train Module 1 (Temporal Behavioral Transformer)

```bash
make data-download
make data-prepare
make train-1
```

All training runs are tracked in MLflow at http://localhost:5000.

---

## Developer Workflow

The `Makefile` covers the full development cycle:

```bash
make dev          # Start all Docker services
make migrate      # Run Alembic migrations
make test         # Run pytest with coverage report
make lint         # ruff + mypy type checking
make format       # Auto-format with ruff
make train-all    # Download data, prepare sequences, train modules 1/2/6
make dbt-run      # Run dbt transformation pipeline
make dbt-test     # Run dbt data quality tests
make clean        # Remove caches and compiled files
```

---

## Data Connectors

AIMA ships with five production-ready connectors. Each implements the `BaseConnector` abstract class and self-registers via the `ConnectorRegistry` decorator pattern.

| Connector | API Version | Data Fetched |
|-----------|------------|--------------|
| Shopify | Admin REST 2024-04 | Customers, orders (cursor-paginated) |
| Klaviyo | v3 (revision 2024-05-15) | Profiles, email events |
| HubSpot | v3 | Contacts, deals, lifecycle stages |
| Meta Ads | Graph API v19.0 | Campaign insights, audiences, purchase actions |
| Google Analytics 4 | Data API v1 | Sessions, conversions, engagement, page performance |

Adding a new connector requires implementing one class with four methods: `validate_credentials`, `fetch_customers`, `fetch_orders`, `fetch_events`.

---

## Background Processing

Six scheduled Celery tasks run automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| `sync_all_connectors` | Every 30 minutes | Pull fresh data from all active connectors |
| `recompute_customer_features` | Every 6 hours | Recompute all 45+ behavioral features |
| `update_churn_predictions` | Daily at 2am | Score all customers with DeepChurnModel |
| `update_brand_sentiment` | Every 15 minutes | Analyze new brand mentions with ABSA |
| `check_segment_drift` | Daily at 6am | Detect and alert on segment composition shifts |
| `generate_weekly_reports` | Monday at 8am | Compile cross-module performance summaries |

Tasks run across four dedicated queues: `sync`, `inference`, `ml`, `reporting`.

---

## Database Schema

TimescaleDB extends PostgreSQL with automatic time-series partitioning. Key tables with their hypertable status:

| Table | Type | Description |
|-------|------|-------------|
| `customers` | Regular | Customer profiles from all connectors |
| `customer_features` | Regular | 45+ computed behavioral features per customer |
| `customer_segments` | Regular | AI-generated segment definitions |
| `customer_segment_memberships` | Regular | Customer-to-segment assignments with transition history |
| `orders` | Hypertable (ordered_at) | Order transactions |
| `customer_events` | Hypertable (created_at) | Behavioral event stream |
| `brand_mentions` | Hypertable (created_at) | Social and review mentions with ABSA scores |
| `campaigns` | Regular | Campaign definitions with predicted and actual metrics |
| `connectors` | Regular | Data source configurations |
| `alerts` | Regular | System-generated alerts and notifications |

Schema versioning is managed with Alembic. Two migrations are included: `001_initial_schema` and `002_add_events_orders_features`.

---

## Monitoring

The Grafana dashboard (auto-provisioned at startup) covers four areas:

**API Health:** Success rate, p95 latency, requests per second, active Celery tasks, per-endpoint latency breakdown, error rate by HTTP status.

**ML Performance:** Inference latency per module (p50/p95), total customers segmented, churn predictions processed.

**Business KPIs:** Customer count by segment over time, brand sentiment score by dimension over time.

**Infrastructure:** Memory usage, CPU usage, Postgres connection count, Redis connected clients.

---

## Research Contributions

AIMA is designed as a research platform. Seven peer-reviewed papers are planned:

| Paper | Target Venue | Core Contribution |
|-------|-------------|-------------------|
| *Dynamic Customer Persona Generation via Temporal Behavioral Transformers* | KDD 2026 | Novel TBT architecture for behavioral fingerprinting |
| *Pre-Launch Campaign Performance Prediction via Multi-Modal Encoding* | WWW 2026 | Multi-task campaign outcome prediction |
| *Conversion-Optimized Content Generation via Outcome-Supervised LLM Fine-Tuning* | ACL 2026 | Brand-voice-conditioned marketing copy generation |
| *Temporal Brand Perception Modeling via Aspect-Level Sentiment Analysis* | Journal of Marketing Research | 10-dimension ABSA for brand monitoring |
| *Unified Causal Attribution: MMM and MTA Reconciliation via Neural Adstock Models* | Marketing Science | Neural MMM with learnable channel parameters |
| *Causal CLV Optimization via Individual Treatment Effect Estimation* | KDD / JMR | Survival analysis for churn and CLV prediction |
| *Towards Autonomous Marketing: Multi-Agent LLM Framework and AIMA-Bench* | AAAI / NeurIPS | Multi-agent AI marketing orchestration and benchmark |

---

## Testing

```bash
make test
```

The test suite covers unit tests for the three most complex subsystems:

- `tests/unit/test_feature_engineer.py` - 15 tests for RFM computation, health score calculation, temporal feature extraction, and feature vector serialization
- `tests/unit/test_clustering.py` - 11 tests for segment naming rules, UMAP+HDBSCAN clustering pipeline, and drift detection logic
- `tests/unit/test_connectors.py` - 13 tests for the base connector interface, connector registry pattern, and data record dataclasses

CI runs the full test suite on every pull request with PostgreSQL and Redis service containers, generating a coverage report.

---

## CI/CD Pipeline

GitHub Actions runs on every push and pull request:

1. **Lint** - `ruff check` and `mypy` type checking
2. **Test** - Full pytest suite with PostgreSQL and Redis services, coverage upload
3. **Build** - Multi-stage Docker build for the API service
4. **Deploy** - `kubectl apply` to Kubernetes on merge to main (requires cluster credentials in GitHub Secrets)

---

## Contributing

AIMA is built to be a community platform. Contributions are welcome across all areas.

**Adding a new AI model:** Follow the pattern in any `modules/*/models/` directory. Each model is a standalone PyTorch module with a `predict()` method.

**Adding a new data connector:** Subclass `BaseConnector` in `data/connectors/`, implement the four required methods, and decorate with `@ConnectorRegistry.register("your_connector")`. It will self-register with no other changes required.

**Adding a new dbt model:** Add a `.sql` file to `data/pipelines/models/staging/` or `data/pipelines/models/marts/`. Run `make dbt-run` to apply.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, branch naming, and PR guidelines.

---

## License

MIT License. Free to use, modify, and distribute. See [LICENSE](LICENSE).
