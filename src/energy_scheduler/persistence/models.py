"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from energy_scheduler.persistence.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DeviceORM(Base):
    """Persisted device record."""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rated_power_w: Mapped[float] = mapped_column(Float, default=0.0)
    interruptibility: Mapped[str] = mapped_column(String(32), default="non_interruptible")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    bindings: Mapped[list[DeviceBindingORM]] = relationship(back_populates="device")
    tasks: Mapped[list[UsageTaskORM]] = relationship(back_populates="device")


class ConnectorORM(Base):
    """Persisted connector integration."""

    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)

    bindings: Mapped[list[DeviceBindingORM]] = relationship(back_populates="connector")


class DeviceBindingORM(Base):
    """Links a device to a connector."""

    __tablename__ = "device_bindings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), nullable=False)
    connector_id: Mapped[str] = mapped_column(ForeignKey("connectors.id"), nullable=False)
    external_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)

    device: Mapped[DeviceORM] = relationship(back_populates="bindings")
    connector: Mapped[ConnectorORM] = relationship(back_populates="bindings")


class UsageTaskORM(Base):
    """A pending device run task."""

    __tablename__ = "usage_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), nullable=False)
    required_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    earliest_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    latest_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5)

    device: Mapped[DeviceORM] = relationship(back_populates="tasks")


class PriceSeriesORM(Base):
    """Cached price series from a provider."""

    __tablename__ = "price_series"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(32), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    native_resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)


class ScheduleORM(Base):
    """A produced schedule result."""

    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    date_label: Mapped[str] = mapped_column(String(16), nullable=False)
    solver: Mapped[str] = mapped_column(String(64), default="greedy_heuristic")
    produced_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    items: Mapped[list[ScheduleItemORM]] = relationship(back_populates="schedule")


class ScheduleItemORM(Base):
    """A single item within a schedule."""

    __tablename__ = "schedule_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    schedule_id: Mapped[str] = mapped_column(ForeignKey("schedules.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    device_id: Mapped[str] = mapped_column(String(36), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estimated_cost_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")

    schedule: Mapped[ScheduleORM] = relationship(back_populates="items")


class CommandHistoryORM(Base):
    """Log of commands sent to devices."""

    __tablename__ = "command_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    device_id: Mapped[str] = mapped_column(String(36), nullable=False)
    external_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    command: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    outcome: Mapped[str] = mapped_column(String(32), default="pending")


class ConsumptionObservationORM(Base):
    """Historical consumption observation."""

    __tablename__ = "consumption_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    device_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
