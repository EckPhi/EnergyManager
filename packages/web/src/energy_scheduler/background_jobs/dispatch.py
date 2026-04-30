"""Schedule execution and command dispatch jobs."""

from __future__ import annotations

from datetime import datetime, timezone


async def dispatch_pending_items() -> None:
    """Dispatch all schedule items that are due to start.

    Idempotent: items already dispatched will have status 'dispatched' and are skipped.
    """
    now = datetime.now(timezone.utc)
    # TODO: load pending ScheduleItemORM records from DB where start_at <= now
    # TODO: for each item, execute_command via the bound connector
    print(f"[dispatch_job] Checking for items due at {now.isoformat()}")


async def sync_device_states() -> None:
    """Poll all bound devices and update their state in the DB."""
    # TODO: iterate bindings, poll_state(), store result
    print("[dispatch_job] Syncing device states")
