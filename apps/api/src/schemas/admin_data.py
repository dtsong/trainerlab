"""Admin data dashboard schemas."""

from pydantic import BaseModel


class TableInfo(BaseModel):
    """Row count and freshness info for a database table."""

    name: str
    row_count: int
    latest_date: str | None = None
    detail: str | None = None


class DataOverviewResponse(BaseModel):
    """Overview of all major database tables."""

    tables: list[TableInfo]
    generated_at: str


class MetaSnapshotSummary(BaseModel):
    """Summary of a meta snapshot for list views."""

    id: str
    snapshot_date: str
    region: str | None = None
    format: str
    best_of: int
    sample_size: int
    archetype_count: int
    diversity_index: float | None = None


class MetaSnapshotListResponse(BaseModel):
    """Paginated list of meta snapshots."""

    items: list[MetaSnapshotSummary]
    total: int


class MetaSnapshotDetailResponse(MetaSnapshotSummary):
    """Full meta snapshot detail including raw JSON fields."""

    archetype_shares: dict
    tier_assignments: dict | None = None
    card_usage: dict | None = None
    jp_signals: dict | None = None
    trends: dict | None = None
    tournaments_included: list[str] | None = None


class PipelineHealthItem(BaseModel):
    """Health status for a single pipeline."""

    name: str
    status: str  # "healthy", "stale", "critical"
    last_run: str | None = None
    days_since_run: int | None = None


class PipelineHealthResponse(BaseModel):
    """Health status for all pipelines."""

    pipelines: list[PipelineHealthItem]
    checked_at: str
