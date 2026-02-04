"""Prediction widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.archetype_prediction import ArchetypePrediction
from src.services.widget_resolvers import register_resolver


@register_resolver("prediction")
class PredictionResolver:
    """Resolves archetype prediction data."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve prediction data.

        Config options:
            archetype_id: Archetype identifier (optional, shows all if not provided)
            limit: Number of predictions to show (default: 5)
            include_past: Include past tournaments (default: false)
        """
        archetype_id = config.get("archetype_id")
        limit = config.get("limit", 5)
        include_past = config.get("include_past", False)

        query = select(ArchetypePrediction).options(
            selectinload(ArchetypePrediction.target_tournament)
        )

        if archetype_id:
            query = query.where(ArchetypePrediction.archetype_id == archetype_id)

        if not include_past:
            query = query.where(ArchetypePrediction.actual_meta_share.is_(None))

        query = query.order_by(ArchetypePrediction.created_at.desc()).limit(limit)

        result = await session.execute(query)
        predictions = list(result.scalars().all())

        if not predictions:
            return {
                "archetype_id": archetype_id,
                "predictions": [],
                "message": "No predictions available",
            }

        formatted_predictions = []
        for pred in predictions:
            formatted_predictions.append(
                {
                    "id": str(pred.id),
                    "archetype_id": pred.archetype_id,
                    "target_tournament": pred.target_tournament.name
                    if pred.target_tournament
                    else None,
                    "tournament_date": pred.target_tournament.date.isoformat()
                    if pred.target_tournament and pred.target_tournament.date
                    else None,
                    "predicted_meta_share": pred.predicted_meta_share,
                    "predicted_day2_rate": pred.predicted_day2_rate,
                    "predicted_tier": pred.predicted_tier,
                    "confidence": float(pred.confidence) if pred.confidence else None,
                    "methodology": pred.methodology,
                    "likely_adaptations": pred.likely_adaptations,
                    "jp_signals": pred.jp_signals,
                    "actual_meta_share": pred.actual_meta_share,
                    "accuracy_score": pred.accuracy_score,
                    "created_at": pred.created_at.isoformat()
                    if pred.created_at
                    else None,
                }
            )

        return {
            "archetype_id": archetype_id,
            "predictions": formatted_predictions,
            "total": len(formatted_predictions),
        }
