"""AI-powered prediction engine for archetype performance forecasting.

Combines historical evolution data, JP meta signals, and upcoming set
releases to predict archetype performance at future tournaments.
"""

import json
import logging
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.claude import MODEL_SONNET, ClaudeClient, ClaudeError
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.meta_snapshot import MetaSnapshot
from src.models.set import Set
from src.models.tournament import Tournament

logger = logging.getLogger(__name__)


class PredictionEngineError(Exception):
    """Error during prediction generation."""


class PredictionEngine:
    """Generates and scores archetype performance predictions."""

    def __init__(self, session: AsyncSession, claude: ClaudeClient) -> None:
        self.session = session
        self.claude = claude

    async def predict(
        self,
        archetype: str,
        target_tournament_id: UUID,
    ) -> ArchetypePrediction:
        """Generate a prediction for an archetype at an upcoming tournament.

        Loads recent snapshots, JP meta data, and upcoming set releases
        to build context, then uses Claude Sonnet to generate predictions.

        Args:
            archetype: Normalized archetype name.
            target_tournament_id: Tournament to predict for.

        Returns:
            An ArchetypePrediction (not yet persisted).

        Raises:
            PredictionEngineError: If prediction fails.
        """
        # Load last 6 snapshots for trajectory
        snapshots = await self._load_recent_snapshots(archetype, limit=6)

        # Get target tournament info
        result = await self.session.execute(
            select(Tournament).where(Tournament.id == target_tournament_id)
        )
        tournament = result.scalar_one_or_none()
        if not tournament:
            raise PredictionEngineError(f"Tournament {target_tournament_id} not found")

        # Get latest meta snapshot for JP signals
        meta_snapshot = await self._get_latest_meta_snapshot()

        # Check for new set releases before tournament date
        new_sets = await self._get_upcoming_sets(tournament.date)

        # Build context for Claude
        context = self._build_prediction_context(
            archetype, snapshots, meta_snapshot, new_sets, tournament
        )

        # Generate prediction via Claude
        try:
            prediction_data = await self._generate_prediction(archetype, context)
        except ClaudeError as e:
            raise PredictionEngineError(f"Failed to generate prediction: {e}") from e

        return ArchetypePrediction(
            id=uuid4(),
            archetype_id=archetype,
            target_tournament_id=target_tournament_id,
            predicted_meta_share=prediction_data.get("predicted_meta_share"),
            predicted_day2_rate=prediction_data.get("predicted_day2_rate"),
            predicted_tier=prediction_data.get("predicted_tier"),
            likely_adaptations=prediction_data.get("likely_adaptations"),
            jp_signals=prediction_data.get("jp_signals"),
            confidence=prediction_data.get("confidence"),
            methodology=prediction_data.get("methodology"),
        )

    async def score_prediction(self, prediction_id: UUID) -> None:
        """Score a prediction after the tournament has occurred.

        Computes accuracy by comparing predicted vs actual meta share.

        Args:
            prediction_id: The prediction to score.

        Raises:
            PredictionEngineError: If scoring fails.
        """
        result = await self.session.execute(
            select(ArchetypePrediction).where(ArchetypePrediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        if not prediction:
            raise PredictionEngineError(f"Prediction {prediction_id} not found")

        # Find the actual snapshot for this archetype at the tournament
        result = await self.session.execute(
            select(ArchetypeEvolutionSnapshot).where(
                ArchetypeEvolutionSnapshot.archetype == prediction.archetype_id,
                ArchetypeEvolutionSnapshot.tournament_id
                == prediction.target_tournament_id,
            )
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            logger.warning(
                "No snapshot found for scoring prediction %s",
                prediction_id,
            )
            return

        prediction.actual_meta_share = snapshot.meta_share

        # Compute accuracy score
        if prediction.predicted_meta_share and prediction.actual_meta_share is not None:
            mid = prediction.predicted_meta_share.get("mid", 0)
            if mid > 0:
                error = abs(prediction.actual_meta_share - mid) / mid
                prediction.accuracy_score = round(max(0, 1.0 - error), 4)

        await self.session.commit()

    async def _load_recent_snapshots(
        self, archetype: str, limit: int = 6
    ) -> list[ArchetypeEvolutionSnapshot]:
        """Load recent snapshots ordered by tournament date."""
        query = (
            select(ArchetypeEvolutionSnapshot)
            .join(
                Tournament,
                ArchetypeEvolutionSnapshot.tournament_id == Tournament.id,
            )
            .where(ArchetypeEvolutionSnapshot.archetype == archetype)
            .order_by(Tournament.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_latest_meta_snapshot(self) -> MetaSnapshot | None:
        """Get the most recent meta snapshot."""
        result = await self.session.execute(
            select(MetaSnapshot).order_by(MetaSnapshot.snapshot_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_upcoming_sets(self, before_date: date) -> list[Set]:
        """Get sets released recently (within 30 days before tournament)."""
        from datetime import timedelta

        cutoff = before_date - timedelta(days=30)
        result = await self.session.execute(
            select(Set).where(
                Set.release_date >= cutoff,
                Set.release_date <= before_date,
            )
        )
        return list(result.scalars().all())

    def _build_prediction_context(
        self,
        archetype: str,
        snapshots: list[ArchetypeEvolutionSnapshot],
        meta_snapshot: MetaSnapshot | None,
        new_sets: list[Set],
        tournament: Tournament,
    ) -> dict:
        """Build the context dict for Claude's prediction prompt."""
        trajectory = []
        for s in snapshots:
            trajectory.append(
                {
                    "meta_share": s.meta_share,
                    "top_cut_conversion": s.top_cut_conversion,
                    "best_placement": s.best_placement,
                    "deck_count": s.deck_count,
                }
            )

        context: dict = {
            "archetype": archetype,
            "trajectory": trajectory,
            "tournament": {
                "tier": tournament.tier,
                "participant_count": tournament.participant_count,
                "date": tournament.date.isoformat(),
            },
        }

        if meta_snapshot:
            top_10 = dict(
                sorted(
                    meta_snapshot.archetype_shares.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            )
            context["meta"] = {
                "top_archetypes": top_10,
                "jp_signals": meta_snapshot.jp_signals,
                "trends": meta_snapshot.trends,
            }

        if new_sets:
            context["new_sets"] = [
                {"name": s.name, "release_date": s.release_date.isoformat()}
                for s in new_sets
                if s.release_date
            ]

        return context

    async def _generate_prediction(
        self,
        archetype: str,
        context: dict,
    ) -> dict:
        """Use Claude to generate the prediction."""
        system_prompt = (
            "You are a Pokemon TCG meta analyst generating predictions "
            "for upcoming tournaments. Analyze the archetype's trajectory, "
            "current meta, JP signals, and new set releases.\n\n"
            "Respond with JSON containing:\n"
            '- "predicted_meta_share": {"low": float, "mid": float, '
            '"high": float}\n'
            '- "predicted_day2_rate": {"low": float, "mid": float, '
            '"high": float}\n'
            '- "predicted_tier": one of "S", "A", "B", "C", "Rogue"\n'
            '- "likely_adaptations": list of {{"type": str, '
            '"description": str, "cards": list}}\n'
            '- "jp_signals": dict with any relevant JP meta signals\n'
            '- "confidence": float 0.0-1.0\n'
            '- "methodology": 2-3 sentence explanation of reasoning'
        )

        user_prompt = (
            f"Predict {archetype}'s performance:\n\n{json.dumps(context, indent=2)}"
        )

        result = await self.claude.classify(
            system=system_prompt,
            user=user_prompt,
            model=MODEL_SONNET,
            max_tokens=1024,
        )

        return result
