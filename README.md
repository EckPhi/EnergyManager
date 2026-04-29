# EnergyManager

An operator-facing Energy Device Scheduler service that intelligently schedules flexible loads (washing machines, EV chargers, heat pumps, dishwashers) into cheap electricity windows while respecting user constraints.

## Overview

EnergyManager fetches real-time and day-ahead electricity prices from multiple providers (Nord Pool, aWATTar, etc.), forecasts device consumption, and produces an optimised daily schedule. A Home Assistant connector translates schedule items into delayed-start or on/off commands.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Web UI (FastAPI + Jinja2)  │  REST API (/api/v1/…)        │
├────────────────────────────┬───────────────────────────────┤
│  Scheduling Service        │  Pricing Service              │
│  (optimizer + heuristics)  │  (providers → transform)      │
├────────────────────────────┴───────────────────────────────┤
│  Connectors (Home Assistant, …)                            │
├────────────────────────────────────────────────────────────┤
│  SQLAlchemy + PostgreSQL  │  Alembic migrations            │
└────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
cp .env.example .env
# edit .env with your credentials

docker compose up -d
```

The UI is available at `http://localhost:8000`.

## Development

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn energy_scheduler.web.app:create_app --factory --reload
```

### Running Tests

```bash
poetry run pytest tests/ -q
```

### Linting & Type Checking

```bash
poetry run ruff check src tests
poetry run mypy src
```

## Configuration

All settings are read from environment variables (see `.env.example`) or a `.env` file in the project root. Settings are validated on startup via Pydantic Settings.

## Provider Integration

- **Nord Pool**: day-ahead hourly prices for Nordic/Baltic markets
- **aWATTar**: Austrian and German spot prices

Pricing data stays in its provider-native format until explicitly converted by `PriceTransformationService` before reaching the scheduler.

## License

Apache-2.0 — see [LICENSE](LICENSE).
