"""AI-powered evolution article generator.

Generates narrative articles about archetype evolution by combining
snapshot data, adaptations, and predictions into readable content.
"""

import logging
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.claude import MODEL_SONNET, ClaudeClient, ClaudeError
from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.evolution_article import EvolutionArticle
from src.models.evolution_article_snapshot import EvolutionArticleSnapshot
from src.models.lab_note import LabNote
from src.models.tournament import Tournament

logger = logging.getLogger(__name__)


class ArticleGeneratorError(Exception):
    """Error during article generation."""


class EvolutionArticleGenerator:
    """Generates and publishes evolution articles using Claude."""

    def __init__(self, session: AsyncSession, claude: ClaudeClient) -> None:
        self.session = session
        self.claude = claude

    async def generate_article(
        self,
        archetype: str,
        limit: int = 6,
    ) -> EvolutionArticle:
        """Generate an evolution article for an archetype.

        Loads snapshots, adaptations, and predictions, then uses Claude
        to generate introduction and conclusion narrative sections.

        Args:
            archetype: Normalized archetype name.
            limit: Maximum number of snapshots to include.

        Returns:
            An EvolutionArticle (not yet persisted).

        Raises:
            ArticleGeneratorError: If generation fails.
        """
        # Load snapshots ordered by tournament date
        snapshots = await self._load_snapshots(archetype, limit)
        if not snapshots:
            raise ArticleGeneratorError(
                f"No snapshots found for archetype '{archetype}'"
            )

        # Load adaptations for all snapshots
        snapshot_ids = [s.id for s in snapshots]
        adaptations = await self._load_adaptations(snapshot_ids)

        # Load prediction if available
        prediction = await self._load_latest_prediction(archetype)

        # Generate narrative content
        try:
            narrative = await self._generate_narrative(
                archetype, snapshots, adaptations, prediction
            )
        except ClaudeError as e:
            raise ArticleGeneratorError(
                f"Failed to generate article narrative: {e}"
            ) from e

        # Create article
        slug = self._generate_slug(archetype)
        title = narrative.get("title", f"{archetype} Evolution Analysis")
        article = EvolutionArticle(
            id=uuid4(),
            archetype_id=archetype,
            slug=slug,
            title=title,
            excerpt=narrative.get("excerpt"),
            introduction=narrative.get("introduction"),
            conclusion=narrative.get("conclusion"),
            status="draft",
        )

        return article

    async def link_snapshots(
        self,
        article: EvolutionArticle,
        snapshot_ids: list[UUID],
    ) -> list[EvolutionArticleSnapshot]:
        """Link snapshots to an article via the junction table.

        Args:
            article: The article to link snapshots to.
            snapshot_ids: Ordered list of snapshot IDs.

        Returns:
            List of EvolutionArticleSnapshot join records.
        """
        links = []
        for position, snapshot_id in enumerate(snapshot_ids):
            link = EvolutionArticleSnapshot(
                article_id=article.id,
                snapshot_id=snapshot_id,
                position=position,
            )
            links.append(link)
        return links

    async def publish_article(self, article_id: UUID) -> LabNote | None:
        """Publish an article and create a summary Lab Note.

        Sets the article status to 'published' and creates a
        corresponding LabNote of type 'archetype_evolution'.

        Args:
            article_id: The article to publish.

        Returns:
            The created LabNote, or None if article not found.

        Raises:
            ArticleGeneratorError: If publishing fails.
        """
        result = await self.session.execute(
            select(EvolutionArticle).where(EvolutionArticle.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            return None

        now = datetime.now(UTC)

        # Update article status
        article.status = "published"
        article.published_at = now

        # Create summary Lab Note
        content = self._build_lab_note_content(article)
        lab_note = LabNote(
            id=uuid4(),
            slug=f"evolution-{article.slug}",
            note_type="archetype_evolution",
            title=article.title,
            summary=article.excerpt,
            content=content,
            status="published",
            is_published=True,
            published_at=now,
            tags=[article.archetype_id, "evolution"],
            related_content={"archetypes": [article.archetype_id]},
        )

        self.session.add(lab_note)
        article.lab_note_id = lab_note.id
        await self.session.commit()

        return lab_note

    async def _load_snapshots(
        self, archetype: str, limit: int
    ) -> list[ArchetypeEvolutionSnapshot]:
        """Load snapshots ordered by tournament date."""
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

    async def _load_adaptations(self, snapshot_ids: list[UUID]) -> list[Adaptation]:
        """Load adaptations for the given snapshots."""
        if not snapshot_ids:
            return []
        result = await self.session.execute(
            select(Adaptation).where(Adaptation.snapshot_id.in_(snapshot_ids))
        )
        return list(result.scalars().all())

    async def _load_latest_prediction(
        self, archetype: str
    ) -> ArchetypePrediction | None:
        """Load the most recent prediction for the archetype."""
        result = await self.session.execute(
            select(ArchetypePrediction)
            .where(ArchetypePrediction.archetype_id == archetype)
            .order_by(ArchetypePrediction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _generate_narrative(
        self,
        archetype: str,
        snapshots: list[ArchetypeEvolutionSnapshot],
        adaptations: list[Adaptation],
        prediction: ArchetypePrediction | None,
    ) -> dict:
        """Use Claude to generate article narrative sections."""
        system_prompt = (
            "You are a Pokemon TCG meta analyst writing an evolution "
            "article for competitive players. Generate engaging, "
            "analytical content.\n\n"
            "Respond with JSON containing:\n"
            '- "title": compelling article title (max 100 chars)\n'
            '- "excerpt": 1-2 sentence preview (max 200 chars)\n'
            '- "introduction": 2-3 paragraph intro covering the '
            "archetype's recent trajectory\n"
            '- "conclusion": 1-2 paragraph conclusion with outlook '
            "and recommendations"
        )

        snapshot_data = []
        for s in snapshots:
            snapshot_data.append(
                {
                    "archetype": s.archetype,
                    "meta_share": s.meta_share,
                    "top_cut_conversion": s.top_cut_conversion,
                    "best_placement": s.best_placement,
                    "deck_count": s.deck_count,
                    "meta_context": s.meta_context,
                }
            )

        adaptation_data = []
        for a in adaptations:
            adaptation_data.append(
                {
                    "type": a.type,
                    "description": a.description,
                    "cards_added": a.cards_added,
                    "cards_removed": a.cards_removed,
                }
            )

        import json

        user_prompt = (
            f"Write an evolution article for {archetype}.\n\n"
            f"Snapshots (most recent first):\n"
            f"{json.dumps(snapshot_data, indent=2)}\n\n"
            f"Adaptations:\n{json.dumps(adaptation_data, indent=2)}"
        )

        if prediction:
            pred_data = {
                "predicted_tier": prediction.predicted_tier,
                "predicted_meta_share": prediction.predicted_meta_share,
                "methodology": prediction.methodology,
            }
            user_prompt += f"\n\nPrediction:\n{json.dumps(pred_data, indent=2)}"

        result = await self.claude.classify(
            system=system_prompt,
            user=user_prompt,
            model=MODEL_SONNET,
            max_tokens=2048,
        )

        return result

    def _generate_slug(self, archetype: str) -> str:
        """Generate a URL slug for the article."""
        base = archetype.lower()
        base = re.sub(r"[^a-z0-9\s-]", "", base)
        base = re.sub(r"[\s]+", "-", base).strip("-")
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        return f"{base}-evolution-{timestamp}"

    def _build_lab_note_content(self, article: EvolutionArticle) -> str:
        """Build markdown content for the summary Lab Note."""
        parts = [f"# {article.title}\n"]

        if article.introduction:
            parts.append(article.introduction)
            parts.append("")

        if article.conclusion:
            parts.append("## Outlook\n")
            parts.append(article.conclusion)

        return "\n".join(parts)
