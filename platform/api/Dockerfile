FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

FROM base AS development
COPY pyproject.toml .
RUN pip install -e ".[dev]"
COPY . .
CMD ["uvicorn", "platform.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
RUN useradd -m -u 1000 aima && chown -R aima:aima /app
USER aima
CMD ["uvicorn", "platform.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
