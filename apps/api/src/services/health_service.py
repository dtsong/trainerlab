"""Pipeline health service.

Queries database for scrape freshness, meta snapshot staleness,
and archetype detection quality metrics.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.models.translated_content import TranslatedContent
from src.schemas.health import (
    ArchetypeHealthDetail,
    MetaHealthDetail,
    MethodTrendDetail,
    PipelineHealthResponse,
    ScrapeHealthDetail,
    SourceHealthDetail,
    TextLabelFallbackDetail,
    UnknownPlacementDetail,
    VerboseArchetypeDetail,
)

logger = logging.getLogger(__name__)

# Thresholds
SCRAPE_OK_DAYS = 3
SCRAPE_STALE_DAYS = 14
META_OK_DAYS = 2
META_STALE_DAYS = 7
ARCHETYPE_UNKNOWN_OK = 0.10
ARCHETYPE_UNKNOWN_DEGRADED = 0.25

SOURCE_OK_DAYS = 7
SOURCE_STALE_DAYS = 21
LIMITLESS_SOURCE_OK_DAYS = 3
LIMITLESS_SOURCE_STALE_DAYS = 14


class PipelineHealthService:
    """Checks pipeline health across scrape, meta, and archetype."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _source_status(
        days: int | None,
        ok_days: int,
        stale_days: int,
    ) -> Literal["ok", "stale", "missing"]:
        if days is None:
            return "missing"
        if days <= ok_days:
            return "ok"
        if days <= stale_days:
            return "stale"
        return "missing"

    async def _safe_last_date(self, stmt) -> date | None:
        """Execute scalar date query and swallow query failures."""
        try:
            result = await self.session.scalar(stmt)
        except Exception:
            logger.exception("Source health query failed")
            return None

        if result is None:
            return None

        if isinstance(result, datetime):
            return result.date()

        if isinstance(result, date):
            return result

        return None

    async def get_source_health(self) -> list[SourceHealthDetail]:
        """Build source-level freshness detail for operators."""
        today = date.today()
        sources: list[SourceHealthDetail] = []

        source_checks = [
            (
                "tcgdex",
                select(func.max(Card.updated_at)),
                SOURCE_OK_DAYS,
                SOURCE_STALE_DAYS,
            ),
            (
                "limitless",
                select(func.max(Tournament.date)).where(
                    Tournament.source == "limitless"
                ),
                LIMITLESS_SOURCE_OK_DAYS,
                LIMITLESS_SOURCE_STALE_DAYS,
            ),
            (
                "rk9",
                select(func.max(Tournament.updated_at)).where(
                    Tournament.event_source == "rk9"
                ),
                SOURCE_OK_DAYS,
                SOURCE_STALE_DAYS,
            ),
            (
                "pokemon_events",
                select(func.max(Tournament.updated_at)).where(
                    Tournament.event_source == "pokemon.com"
                ),
                SOURCE_OK_DAYS,
                SOURCE_STALE_DAYS,
            ),
            (
                "pokecabook",
                select(func.max(TranslatedContent.updated_at)).where(
                    func.lower(TranslatedContent.source_name) == "pokecabook"
                ),
                SOURCE_OK_DAYS,
                SOURCE_STALE_DAYS,
            ),
            (
                "pokekameshi",
                select(func.max(TranslatedContent.updated_at)).where(
                    func.lower(TranslatedContent.source_name) == "pokekameshi"
                ),
                SOURCE_OK_DAYS,
                SOURCE_STALE_DAYS,
            ),
        ]

        for source_name, query, ok_days, stale_days in source_checks:
            last_date = await self._safe_last_date(query)
            age_days = (today - last_date).days if last_date else None
            status = self._source_status(age_days, ok_days, stale_days)

            failure_reason = None
            if status == "stale":
                failure_reason = "source_data_stale"
            elif status == "missing":
                failure_reason = "no_recent_source_data"

            sources.append(
                SourceHealthDetail(
                    source=source_name,
                    status=status,
                    last_success_at=last_date.isoformat() if last_date else None,
                    age_days=age_days,
                    failure_reason=failure_reason,
                )
            )

        return sources

    async def get_scrape_health(self) -> ScrapeHealthDetail:
        """Query Tournament for scrape freshness."""
        today = date.today()
        seven_days_ago = today - timedelta(days=7)

        # Latest tournament by created_at
        result = await self.session.execute(
            select(
                func.max(Tournament.created_at),
                func.count(Tournament.id).filter(
                    Tournament.created_at
                    >= datetime(
                        seven_days_ago.year,
                        seven_days_ago.month,
                        seven_days_ago.day,
                        tzinfo=UTC,
                    )
                ),
            )
        )
        row = result.one()
        last_scrape = row[0]
        count_7d = row[1] or 0

        # Distinct regions
        region_result = await self.session.execute(
            select(func.distinct(Tournament.region))
        )
        regions = [r[0] for r in region_result.all() if r[0]]

        if last_scrape is None:
            return ScrapeHealthDetail(status="missing", regions=regions)

        days_since = (datetime.now(UTC) - last_scrape.replace(tzinfo=UTC)).days

        if days_since <= SCRAPE_OK_DAYS:
            status = "ok"
        elif days_since <= SCRAPE_STALE_DAYS:
            status = "stale"
        else:
            status = "missing"

        return ScrapeHealthDetail(
            status=status,
            last_scrape_date=last_scrape.isoformat(),
            days_since_scrape=days_since,
            tournament_count_7d=count_7d,
            regions=regions,
        )

    async def get_meta_health(self) -> MetaHealthDetail:
        """Query MetaSnapshot for freshness."""
        result = await self.session.execute(
            select(func.max(MetaSnapshot.snapshot_date))
        )
        latest_date = result.scalar()

        # Distinct regions
        region_result = await self.session.execute(
            select(func.distinct(MetaSnapshot.region))
        )
        regions = [r[0] if r[0] else "Global" for r in region_result.all()]

        if latest_date is None:
            return MetaHealthDetail(status="missing", regions=regions)

        age_days = (date.today() - latest_date).days

        if age_days <= META_OK_DAYS:
            status = "ok"
        elif age_days <= META_STALE_DAYS:
            status = "stale"
        else:
            status = "missing"

        return MetaHealthDetail(
            status=status,
            latest_snapshot_date=latest_date.isoformat(),
            snapshot_age_days=age_days,
            regions=regions,
        )

    async def get_archetype_health(
        self,
    ) -> ArchetypeHealthDetail:
        """Query 30-day placements for detection quality."""
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        result = await self.session.execute(
            select(
                TournamentPlacement.archetype,
                TournamentPlacement.archetype_detection_method,
            ).where(TournamentPlacement.created_at >= thirty_days_ago)
        )
        rows = result.all()

        if not rows:
            return ArchetypeHealthDetail(status="ok", sample_size=0)

        total = len(rows)
        unknown_count = sum(1 for arch, _method in rows if arch == "Unknown")
        rogue_count = sum(1 for arch, _method in rows if arch == "Rogue")
        method_counts: Counter[str] = Counter(
            method or "none" for _arch, method in rows
        )

        unknown_rate = unknown_count / total
        rogue_rate = rogue_count / total
        method_dist = {m: c / total for m, c in method_counts.items()}

        # Find uncovered sprite keys (text_label placements
        # that aren't "Unknown" or "Rogue")
        text_label_archetypes = set()
        for arch, method in rows:
            if method == "text_label" and arch not in ("Unknown", "Rogue"):
                text_label_archetypes.add(arch)

        # These are archetypes that fell through to text_label
        # — candidates for adding to sprite map
        uncovered = sorted(text_label_archetypes)[:20]

        if unknown_rate <= ARCHETYPE_UNKNOWN_OK:
            status = "ok"
        elif unknown_rate <= ARCHETYPE_UNKNOWN_DEGRADED:
            status = "degraded"
        else:
            status = "poor"

        return ArchetypeHealthDetail(
            status=status,
            unknown_rate=round(unknown_rate, 4),
            rogue_rate=round(rogue_rate, 4),
            method_distribution={k: round(v, 4) for k, v in method_dist.items()},
            uncovered_sprite_keys=uncovered,
            sample_size=total,
        )

    async def get_verbose_archetype_detail(
        self,
    ) -> VerboseArchetypeDetail:
        """Get verbose archetype diagnostics."""
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Last 10 Unknown placements with context
        unknown_query = (
            select(
                Tournament.source_url,
                TournamentPlacement.raw_archetype_sprites,
                TournamentPlacement.raw_archetype,
                TournamentPlacement.archetype_detection_method,
            )
            .join(
                Tournament,
                TournamentPlacement.tournament_id == Tournament.id,
            )
            .where(
                TournamentPlacement.archetype == "Unknown",
                TournamentPlacement.created_at >= thirty_days_ago,
            )
            .order_by(TournamentPlacement.created_at.desc())
            .limit(10)
        )
        unknown_result = await self.session.execute(unknown_query)
        unknown_placements = [
            UnknownPlacementDetail(
                tournament_url=row[0],
                sprite_urls=row[1] or [],
                raw_archetype=row[2],
                detection_method=row[3],
            )
            for row in unknown_result.all()
        ]

        # Recent text_label fallbacks with counts
        text_query = (
            select(
                TournamentPlacement.archetype,
                func.count(TournamentPlacement.id).label("cnt"),
            )
            .where(
                TournamentPlacement.archetype_detection_method == "text_label",
                TournamentPlacement.archetype.notin_(["Unknown", "Rogue"]),
                TournamentPlacement.created_at >= thirty_days_ago,
            )
            .group_by(TournamentPlacement.archetype)
            .order_by(func.count(TournamentPlacement.id).desc())
            .limit(20)
        )
        text_result = await self.session.execute(text_query)
        text_fallbacks = [
            TextLabelFallbackDetail(
                sprite_key="",
                resolved_archetype=row[0],
                count=row[1],
            )
            for row in text_result.all()
        ]

        # 7-day rolling detection method distribution
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        trend_query = (
            select(
                func.date(TournamentPlacement.created_at).label("day"),
                TournamentPlacement.archetype_detection_method,
                func.count(TournamentPlacement.id).label("cnt"),
            )
            .where(TournamentPlacement.created_at >= seven_days_ago)
            .group_by(
                func.date(TournamentPlacement.created_at),
                TournamentPlacement.archetype_detection_method,
            )
            .order_by(func.date(TournamentPlacement.created_at))
        )
        trend_result = await self.session.execute(trend_query)
        trend_rows = trend_result.all()

        # Aggregate by day
        day_totals: dict[str, dict[str, int]] = {}
        for day, method, cnt in trend_rows:
            day_str = str(day)
            if day_str not in day_totals:
                day_totals[day_str] = {}
            day_totals[day_str][method or "none"] = cnt

        method_trends = []
        for day_str, methods in sorted(day_totals.items()):
            total = sum(methods.values())
            if total == 0:
                continue
            method_trends.append(
                MethodTrendDetail(
                    date=day_str,
                    sprite_lookup=round(methods.get("sprite_lookup", 0) / total, 4),
                    auto_derive=round(methods.get("auto_derive", 0) / total, 4),
                    signature_card=round(
                        methods.get("signature_card", 0) / total,
                        4,
                    ),
                    text_label=round(methods.get("text_label", 0) / total, 4),
                )
            )

        return VerboseArchetypeDetail(
            unknown_placements=unknown_placements,
            text_label_fallbacks=text_fallbacks,
            method_trends=method_trends,
        )

    async def get_pipeline_health(
        self,
        verbose: bool = False,
    ) -> PipelineHealthResponse:
        """Aggregate all health checks."""
        scrape = await self.get_scrape_health()
        meta = await self.get_meta_health()
        archetype = await self.get_archetype_health()
        sources = await self.get_source_health()

        # Overall status: worst of all components
        scrape_severity = {
            "ok": 0,
            "stale": 1,
            "missing": 2,
        }
        meta_severity = {
            "ok": 0,
            "stale": 1,
            "missing": 2,
        }
        archetype_severity = {
            "ok": 0,
            "degraded": 1,
            "poor": 2,
        }

        max_severity = max(
            scrape_severity.get(scrape.status, 2),
            meta_severity.get(meta.status, 2),
            archetype_severity.get(archetype.status, 2),
        )

        if max_severity == 0:
            overall = "healthy"
        elif max_severity == 1:
            overall = "degraded"
        else:
            overall = "unhealthy"

        verbose_detail = None
        if verbose:
            verbose_detail = await self.get_verbose_archetype_detail()

        return PipelineHealthResponse(
            status=overall,
            scrape=scrape,
            meta=meta,
            archetype=archetype,
            sources=sources,
            checked_at=datetime.now(UTC),
            verbose=verbose_detail,
        )
