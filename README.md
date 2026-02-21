# AIMA — Artificial Intelligence for Marketing Analytics

> **Open Source | Free Forever | Built for Every Marketer on Earth**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C.svg)](https://pytorch.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

AIMA is the world's first open-source, end-to-end AI marketing intelligence platform. It gives every marketer — from a solo freelancer to an enterprise team — access to the kind of AI-powered marketing intelligence that currently only Fortune 500 companies can afford.

---

## What AIMA Does

AIMA solves 7 core marketing problems with 7 AI-powered modules:

| Module | What It Solves |
|--------|---------------|
| **Customer Intelligence Engine** | Deep behavioral segmentation beyond RFM |
| **Campaign Performance Predictor** | Know if your campaign will work *before* you launch |
| **AI Content Studio** | Generate marketing content that actually converts |
| **Brand Intelligence Monitor** | Know what the market really thinks about you |
| **Marketing Attribution Engine** | Know what's actually driving your revenue |
| **CLV & Churn Intelligence Hub** | Keep the customers worth keeping |
| **Autonomous AI Marketing Agent** | Your AI marketing team |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend)

### Launch locally in 3 commands

```bash
git clone https://github.com/your-org/aima.git
cd aima
cp .env.example .env
docker-compose up
```

AIMA will be running at:
- **API:** http://localhost:8000
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **MLflow:** http://localhost:5000
- **Grafana:** http://localhost:3001

### Connect your first data source

```bash
curl -X POST http://localhost:8000/api/v1/connectors/shopify \
  -H "Content-Type: application/json" \
  -d '{"shop_domain": "your-store.myshopify.com", "api_key": "your-key"}'
```

### Run your first customer segmentation

```bash
curl -X POST http://localhost:8000/api/v1/modules/customer-intelligence/segment \
  -H "Content-Type: application/json" \
  -d '{"connector_id": "shopify-1", "n_segments": "auto"}'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Layer                        │
│          Dashboard (Next.js) + REST API + CLI            │
├─────────────────────────────────────────────────────────┤
│                     Action Layer                          │
│      Campaign Launcher · Audience Export · Alerts        │
├─────────────────────────────────────────────────────────┤
│                   Intelligence Layer                      │
│  M1: Customer  M2: Campaign  M3: Content  M4: Brand     │
│  M5: Attribution  M6: CLV/Churn  M7: AI Agent           │
├─────────────────────────────────────────────────────────┤
│                  Data Ingestion Layer                     │
│   Shopify · HubSpot · Meta Ads · GA4 · Klaviyo · ...    │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

**Data:** PostgreSQL + TimescaleDB · Redis · Apache Kafka · dbt · MinIO

**AI/ML:** PyTorch · HuggingFace · LangChain + LangGraph · PyMC · CausalML · scikit-learn

**Backend:** FastAPI · Celery · SQLAlchemy · Pydantic · Alembic

**Frontend:** Next.js 14 · Tailwind CSS · Recharts · D3.js

**Infrastructure:** Docker · Kubernetes (Helm) · GitHub Actions · Prometheus · Grafana

---

## Module Documentation

- [Module 1 — Customer Intelligence Engine](docs/modules/customer-intelligence.md)
- [Module 2 — Campaign Performance Predictor](docs/modules/campaign-predictor.md)
- [Module 3 — AI Content Studio](docs/modules/content-studio.md)
- [Module 4 — Brand Intelligence Monitor](docs/modules/brand-monitor.md)
- [Module 5 — Marketing Attribution Engine](docs/modules/attribution.md)
- [Module 6 — CLV & Churn Intelligence Hub](docs/modules/clv-churn.md)
- [Module 7 — Autonomous AI Marketing Agent](docs/modules/agent.md)

---

## Research Papers

AIMA is built to produce academic research. 7 papers are planned from the platform:

1. *Dynamic Customer Persona Generation via Temporal Behavioral Transformers* — KDD 2026
2. *Pre-Launch Campaign Performance Prediction via Multi-Modal Encoding* — WWW 2026
3. *Conversion-Optimized Content Generation via Outcome-Supervised LLM Fine-Tuning* — ACL 2026
4. *Temporal Brand Perception Modeling via Aspect-Level Sentiment Analysis* — JMR
5. *Unified Causal Attribution: MMM and MTA Reconciliation* — Marketing Science / KDD
6. *Causal CLV Optimization: Individual Treatment Effect Estimation* — KDD / JMR
7. *Towards Autonomous Marketing: Multi-Agent LLM Framework + AIMA-Bench* — AAAI / NeurIPS

---

## Contributing

AIMA is community-built. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

**Good first issues:** Look for the `good-first-issue` label on GitHub.

**New integrations:** See [docs/contributing/new-connector.md](docs/contributing/new-connector.md) to add a new data source.

---

## License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## Community

- **Discord:** [Join the AIMA community](https://discord.gg/aima)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/aima/discussions)
- **Twitter/X:** [@AIMAplatform](https://twitter.com/AIMAplatform)
