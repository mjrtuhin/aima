# Contributing to AIMA

Thank you for wanting to contribute to AIMA. This guide covers everything you need to get started.

---

## Ways to Contribute

- **Fix bugs** — look for `bug` labels on GitHub Issues
- **Build new features** — look for `enhancement` labels
- **Add a new data connector** — any platform AIMA doesn't yet support
- **Improve documentation** — fix typos, add examples, improve clarity
- **Write tests** — increase test coverage across any module
- **Research** — contribute to the academic papers in `research/`

---

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/your-username/aima.git
cd aima
```

### 2. Set up your environment

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### 3. Start the local stack

```bash
docker-compose up -d postgres redis kafka minio mlflow
```

### 4. Run the tests

```bash
pytest tests/
```

---

## Code Standards

- **Python:** Formatted with `ruff`, typed with `mypy`
- **Commits:** Use conventional commits — `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- **Tests:** Every new feature needs unit tests. Every bug fix needs a regression test.
- **No commented-out code** in pull requests.

---

## Adding a New Data Connector

1. Create a folder under `data/connectors/<platform_name>/`
2. Implement `connector.py` with the `BaseConnector` interface from `data/connectors/base.py`
3. Add a schema file `data/schemas/<platform_name>.json`
4. Add tests in `tests/unit/connectors/test_<platform_name>.py`
5. Add documentation in `docs/contributing/connectors/<platform_name>.md`
6. Submit a PR with the title `feat(connector): add <platform_name> connector`

---

## Pull Request Process

1. Create a branch: `git checkout -b feat/your-feature-name`
2. Make your changes with tests
3. Run `ruff check .` and `mypy .` — both must pass
4. Run `pytest tests/` — all tests must pass
5. Submit a PR against `main` with a clear description
6. A maintainer will review within 48 hours

---

## Architecture Decision Records (ADRs)

Major technical decisions are documented in `docs/contributing/` as ADRs. If your PR changes the architecture, write an ADR explaining the decision, the alternatives considered, and why you chose this approach.

---

## Code of Conduct

AIMA is for every marketer on earth. We expect all contributors to be respectful and inclusive. Harassment of any kind will not be tolerated.

---

## Questions?

Open a GitHub Discussion or join the Discord. We're happy to help.
