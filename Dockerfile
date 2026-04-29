FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry==1.8.* && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root --only main

FROM base AS runtime
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src/ ./src/
COPY alembic.ini ./

RUN pip install --no-deps -e .

EXPOSE 8000
CMD ["uvicorn", "energy_scheduler.web.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
