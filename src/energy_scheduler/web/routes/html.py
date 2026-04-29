"""Template-rendering routes."""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])

_templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=_templates_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/devices", response_class=HTMLResponse)
async def devices(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("devices.html", {"request": request, "devices": []})


@router.get("/provider", response_class=HTMLResponse)
async def provider(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("provider.html", {"request": request})


@router.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("schedule.html", {"request": request, "items": []})
