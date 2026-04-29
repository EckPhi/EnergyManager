"""FastAPI application factory."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from energy_scheduler.web.routes.api import router as api_router
from energy_scheduler.web.routes.html import router as html_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from energy_scheduler.config import get_settings
    from energy_scheduler.logging import configure_logging

    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="EnergyManager",
        version="0.1.0",
        description="Intelligent energy device scheduler",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(html_router)
    app.include_router(api_router, prefix="/api/v1")

    return app


def main() -> None:
    """CLI entry point."""
    import uvicorn
    uvicorn.run("energy_scheduler.web.app:create_app", factory=True, host="0.0.0.0", port=8000)
