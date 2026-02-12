"""Helpers for cadence-aware data freshness evaluation."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from src.schemas.freshness import CadenceProfile, DataFreshness


def _next_tuesday(event_end: date) -> date:
    """Return the next Tuesday on or after event_end."""
    tuesday = 1  # Monday=0, Tuesday=1
    delta = (tuesday - event_end.weekday()) % 7
    return event_end + timedelta(days=delta)


def build_data_freshness(
    *,
    cadence_profile: CadenceProfile,
    snapshot_date: date | None,
    sample_size: int | None = None,
    source_coverage: list[str] | None = None,
    latest_tpci_event_end_date: date | None = None,
    now_utc: datetime | None = None,
) -> DataFreshness:
    """Build freshness payload from cadence and latest data markers."""
    now = now_utc or datetime.now(UTC)
    today = now.date()

    if snapshot_date is None:
        return DataFreshness(
            status="no_data",
            cadence_profile=cadence_profile,
            snapshot_date=None,
            sample_size=sample_size,
            staleness_days=None,
            source_coverage=source_coverage,
            message="No data snapshot is available yet.",
        )

    staleness_days = max(0, (today - snapshot_date).days)
    size = sample_size if sample_size is not None else 0

    if cadence_profile == "tpci_event_cadence":
        deadline_missed = False
        if latest_tpci_event_end_date is not None:
            tpci_deadline = _next_tuesday(latest_tpci_event_end_date)
            deadline_missed = (
                today > tpci_deadline and snapshot_date < latest_tpci_event_end_date
            )

        if size >= 64 and not deadline_missed:
            status = "fresh"
            message = "TPCI post-major snapshot is up to date."
        elif size >= 8:
            status = "partial"
            message = "Post-major data is in early state (top cut only)."
        elif deadline_missed:
            status = "stale"
            message = (
                "Major-event update expected by Tuesday UTC; latest "
                "snapshot is older than target."
            )
        elif size > 0:
            status = "partial"
            message = "Early post-major data is available; full ingest in progress."
        else:
            status = "no_data"
            message = "No post-major dataset is available yet."

        return DataFreshness(
            status=status,
            cadence_profile=cadence_profile,
            snapshot_date=snapshot_date,
            sample_size=sample_size,
            staleness_days=staleness_days,
            source_coverage=source_coverage,
            message=message,
        )

    if cadence_profile == "jp_daily_cadence":
        fresh_days, stale_days = 2, 6
        partial_threshold = 24
        cadence_label = "JP daily"
    elif cadence_profile == "grassroots_daily_cadence":
        fresh_days, stale_days = 3, 10
        partial_threshold = 24
        cadence_label = "grassroots"
    else:
        fresh_days, stale_days = 3, 10
        partial_threshold = 24
        cadence_label = "default"

    if size > 0 and size < partial_threshold:
        status = "partial"
        message = (
            f"{cadence_label.capitalize()} dataset is available but has limited sample."
        )
    elif staleness_days <= fresh_days:
        status = "fresh"
        message = "Data snapshot is current."
    elif staleness_days <= stale_days:
        status = "stale"
        message = "Data may be stale for this cadence."
    else:
        status = "no_data"
        message = "No recent data available for this cadence window."

    return DataFreshness(
        status=status,
        cadence_profile=cadence_profile,
        snapshot_date=snapshot_date,
        sample_size=sample_size,
        staleness_days=staleness_days,
        source_coverage=source_coverage,
        message=message,
    )
