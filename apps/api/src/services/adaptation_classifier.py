"""AI-powered adaptation classifier and meta context generator.

Uses Claude to classify adaptations and generate human-readable
meta context explanations for archetype evolution snapshots.
"""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.claude import MODEL_HAIKU, MODEL_SONNET, ClaudeClient, ClaudeError
from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.meta_snapshot import MetaSnapshot

logger = logging.getLogger(__name__)


class AdaptationClassifierError(Exception):
    """Error during adaptation classification."""


class AdaptationClassifier:
    """Classifies adaptations and generates meta context using Claude."""

    def __init__(self, session: AsyncSession, claude: ClaudeClient) -> None:
        self.session = session
        self.claude = claude

    async def classify(
        self,
        adaptation: Adaptation,
        meta_context: dict | None = None,
    ) -> Adaptation:
        """Classify an adaptation using Claude Haiku.

        Updates the adaptation's type, description, prevalence, confidence,
        and target_archetype fields based on AI analysis.

        Args:
            adaptation: The adaptation to classify.
            meta_context: Optional dict with current meta info (top archetypes,
                recent trends) to help Claude understand the context.

        Returns:
            The updated Adaptation with classification fields populated.

        Raises:
            AdaptationClassifierError: If classification fails.
        """
        system_prompt = (
            "You are a Pokemon TCG meta analyst. Classify the following "
            "card change (adaptation) in a competitive deck.\n\n"
            "Respond with JSON containing:\n"
            '- "type": one of "tech", "consistency", "engine", "removal"\n'
            "  - tech: a card added to counter a specific matchup\n"
            "  - consistency: a count change to improve draw/search\n"
            "  - engine: a core combo piece change\n"
            "  - removal: a card dropped from the list\n"
            '- "description": 1-2 sentence explanation of why this change '
            "was made\n"
            '- "target_archetype": if type is "tech", which archetype '
            "this targets (or null)\n"
            '- "confidence": float 0.0-1.0 for how confident this '
            "classification is\n"
            '- "prevalence": float 0.0-1.0 for how widespread this '
            "change is in the meta"
        )

        change_info = {
            "cards_added": adaptation.cards_added,
            "cards_removed": adaptation.cards_removed,
            "current_type": adaptation.type,
            "current_description": adaptation.description,
        }

        user_prompt = f"Card change:\n{json.dumps(change_info, indent=2)}"
        if meta_context:
            user_prompt += (
                f"\n\nCurrent meta context:\n{json.dumps(meta_context, indent=2)}"
            )

        try:
            result = await self.claude.classify(
                system=system_prompt,
                user=user_prompt,
                model=MODEL_HAIKU,
                max_tokens=512,
            )

            adaptation.type = result.get("type", adaptation.type)
            adaptation.description = result.get("description", adaptation.description)
            adaptation.confidence = result.get("confidence")
            adaptation.prevalence = result.get("prevalence")
            adaptation.target_archetype = result.get("target_archetype")
            adaptation.source = "claude"

            return adaptation

        except ClaudeError as e:
            raise AdaptationClassifierError(
                f"Failed to classify adaptation: {e}"
            ) from e

    async def generate_meta_context(
        self,
        snapshot: ArchetypeEvolutionSnapshot,
        adaptations: list[Adaptation],
        meta_snapshot: MetaSnapshot | None = None,
    ) -> str:
        """Generate a human-readable meta context for a snapshot.

        Produces a 2-3 sentence explanation of why the archetype
        evolved this way, considering the current meta landscape.

        Args:
            snapshot: The evolution snapshot to explain.
            adaptations: Adaptations detected for this snapshot.
            meta_snapshot: Optional current meta snapshot for context.

        Returns:
            A 2-3 sentence meta context string.

        Raises:
            AdaptationClassifierError: If generation fails.
        """
        system_prompt = (
            "You are a Pokemon TCG meta analyst writing for competitive "
            "players. Generate a concise 2-3 sentence explanation of why "
            "this archetype evolved this way at this tournament.\n\n"
            "Focus on:\n"
            "- What meta threats drove the changes\n"
            "- How the adaptations improve specific matchups\n"
            "- Any broader meta trends reflected\n\n"
            "Write in present tense, analytical tone. "
            "Do not use markdown formatting."
        )

        snapshot_data = {
            "archetype": snapshot.archetype,
            "meta_share": snapshot.meta_share,
            "top_cut_conversion": snapshot.top_cut_conversion,
            "best_placement": snapshot.best_placement,
            "deck_count": snapshot.deck_count,
        }

        adaptations_data = []
        for a in adaptations:
            adaptations_data.append(
                {
                    "type": a.type,
                    "description": a.description,
                    "cards_added": a.cards_added,
                    "cards_removed": a.cards_removed,
                    "target_archetype": a.target_archetype,
                }
            )

        meta_data = None
        if meta_snapshot:
            top_10 = dict(
                sorted(
                    meta_snapshot.archetype_shares.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            )
            meta_data = {
                "top_archetypes": top_10,
                "jp_signals": meta_snapshot.jp_signals,
                "trends": meta_snapshot.trends,
            }

        user_prompt = (
            f"Snapshot:\n{json.dumps(snapshot_data, indent=2)}\n\n"
            f"Adaptations:\n{json.dumps(adaptations_data, indent=2)}"
        )
        if meta_data:
            user_prompt += f"\n\nMeta landscape:\n{json.dumps(meta_data, indent=2)}"

        try:
            return await self.claude.generate(
                system=system_prompt,
                user=user_prompt,
                model=MODEL_SONNET,
                max_tokens=512,
            )
        except ClaudeError as e:
            raise AdaptationClassifierError(
                f"Failed to generate meta context: {e}"
            ) from e

    async def classify_and_contextualize(
        self,
        snapshot_id: UUID,
    ) -> str | None:
        """Classify all adaptations for a snapshot and generate meta context.

        Convenience method that loads the snapshot and its adaptations,
        classifies each, then generates an overall meta context.

        Args:
            snapshot_id: The snapshot to process.

        Returns:
            Generated meta context string, or None if no adaptations.
        """
        result = await self.session.execute(
            select(ArchetypeEvolutionSnapshot).where(
                ArchetypeEvolutionSnapshot.id == snapshot_id
            )
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return None

        result = await self.session.execute(
            select(Adaptation).where(Adaptation.snapshot_id == snapshot_id)
        )
        adaptations = list(result.scalars().all())

        if not adaptations:
            return None

        # Get latest meta snapshot for context
        result = await self.session.execute(
            select(MetaSnapshot).order_by(MetaSnapshot.snapshot_date.desc()).limit(1)
        )
        meta_snapshot = result.scalar_one_or_none()

        meta_ctx = None
        if meta_snapshot:
            top_10 = dict(
                sorted(
                    meta_snapshot.archetype_shares.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            )
            meta_ctx = {
                "top_archetypes": top_10,
                "jp_signals": meta_snapshot.jp_signals,
            }

        # Classify each adaptation
        for adaptation in adaptations:
            await self.classify(adaptation, meta_context=meta_ctx)

        # Generate meta context
        context = await self.generate_meta_context(snapshot, adaptations, meta_snapshot)

        # Save to snapshot
        snapshot.meta_context = context
        await self.session.commit()

        return context
