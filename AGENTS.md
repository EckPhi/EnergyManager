# AGENTS.md — Cloud-Agent Execution Guide

## Repo Conventions

- **Language**: Python ≥ 3.12 with full type annotations.
- **Layout**: `src/` layout — package root is `src/energy_scheduler/`.
- **Formatter / linter**: Ruff (`ruff check` + `ruff format`). Never silence rules without a comment.
- **Type checker**: mypy in strict mode for the `src/` tree.
- **Tests**: pytest; unit tests live in `tests/unit/`, integration in `tests/integration/`, end-to-end in `tests/e2e/`.
- **Docstrings**: Google style for all public symbols.

## Package Boundaries

| Package | Responsibility | Must NOT import |
|---|---|---|
| `domain/` | Pure data models, no I/O | anything outside `domain/` |
| `pricing/` | Fetch + transform prices | `scheduling`, `connectors`, `web` |
| `scheduling/` | Optimise schedules | `connectors`, `web`, `pricing` providers |
| `connectors/` | Device I/O | `web`, `scheduling` internals |
| `persistence/` | DB access | `web`, business logic |
| `web/` | HTTP layer | direct DB access (use repos) |
| `background_jobs/` | Periodic tasks | `web` |

## Pricing Contract (Critical)

`PriceSeries` (provider-native) and `SchedulerPriceSeries` (scheduler-ready) are **separate types**.
The optimizer **must never** consume a `PriceSeries` directly.
All price data must pass through `PriceTransformationService` before reaching the scheduler.

## Scheduler Grid

Default grid is **15 minutes**. All schedule items are snapped to this grid.
`ScheduleRequest.scheduler_grid_minutes` can override the default per-request.

## Allowed Dependencies

Add new third-party packages only if they are:
1. Listed in `pyproject.toml` already, **or**
2. Strictly necessary and approved via PR description.

Do **not** add heavyweight ML frameworks (PyTorch, TensorFlow) to the main service; isolate them behind a service boundary in `forecasting/`.

## Branching & Editing

- Work on feature branches: `feat/<short-description>`.
- Each commit must pass `ruff check` and `mypy` (CI enforces this).
- Do not force-push to `main`.
- Migration files in `persistence/migrations/versions/` are append-only.

## Testing Expectations

- Unit tests must be self-contained (no network, no DB).
- Use `pytest-asyncio` for async tests.
- Use `respx` for mocking HTTP calls in unit/integration tests.
- Aim for ≥ 80 % branch coverage on `scheduling/` and `pricing/`.

## Background Jobs

Jobs in `background_jobs/` are triggered externally (cron / APScheduler).
Each job function must be idempotent.
