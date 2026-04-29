"""Versioned JSON API routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/providers")
async def list_providers() -> dict[str, list[str]]:
    """List all registered price providers."""
    from energy_scheduler.pricing.registry import get_registry
    registry = get_registry()
    return {"providers": registry.list_providers()}
