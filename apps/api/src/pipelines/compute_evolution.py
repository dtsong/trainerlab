"""Evolution intelligence pipeline.

Daily pipeline that runs AI-powered evolution analysis:
classifies adaptations, generates meta context, updates predictions,
and generates evolution articles.
"""

import logging
from dataclasses import dataclass, field
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from src.clients.claude import ClaudeClient, ClaudeError
from src.db.database import async_session_factory
from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.tournament import Tournament
from src.services.adaptation_classifier import (
    AdaptationClassifier,
    AdaptationClassifierError,
)
from src.services.evolution_article_generator import (
    ArticleGeneratorError,
    EvolutionArticleGenerator,
)
from src.services.prediction_engine import PredictionEngine, PredictionEngineError

logger = logging.getLogger(__name__)


@dataclass
class ComputeEvolutionResult:
    """Result of compute_evolution pipeline."""

    adaptations_classified: int = 0
    contexts_generated: int = 0
    predictions_generated: int = 0
    articles_generated: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def compute_evolution_intelligence(
    dry_run: bool = False,
) -> ComputeEvolutionResult:
    """Run the full evolution intelligence pipeline.

    Steps:
    1. Find unclassified adaptations and classify with Claude
    2. Generate meta_context for snapshots missing it
    3. Generate/update predictions for upcoming major events
    4. Generate/update evolution articles for active archetypes

    Args:
        dry_run: If true, skip persistence steps.

    Returns:
        ComputeEvolutionResult with pipeline statistics.
    """
    result = ComputeEvolutionResult()

    try:
        async with ClaudeClient() as claude, async_session_factory() as session:
            classifier = AdaptationClassifier(session, claude)
            prediction_engine = PredictionEngine(session, claude)
            article_generator = EvolutionArticleGenerator(session, claude)

            # Step 1: Classify unclassified adaptations
            await _classify_adaptations(session, classifier, result, dry_run)

            # Step 2: Generate meta context for snapshots missing it
            await _generate_meta_contexts(session, classifier, result, dry_run)

            # Step 3: Generate predictions for upcoming tournaments
            await _generate_predictions(session, prediction_engine, result, dry_run)

            # Step 4: Generate evolution articles
            await _generate_articles(session, article_generator, result, dry_run)

    except SQLAlchemyError as e:
        logger.error("Database error in evolution pipeline: %s", e, exc_info=True)
        result.errors.append(f"Database error: {e}")
    except ClaudeError as e:
        logger.error("Claude API error in evolution pipeline: %s", e, exc_info=True)
        result.errors.append(f"Claude API error: {e}")
    except Exception as e:
        logger.error("Unexpected error in evolution pipeline: %s", e, exc_info=True)
        result.errors.append(f"Unexpected error: {e}")

    logger.info(
        "Evolution pipeline complete: classified=%d, contexts=%d, "
        "predictions=%d, articles=%d, errors=%d",
        result.adaptations_classified,
        result.contexts_generated,
        result.predictions_generated,
        result.articles_generated,
        len(result.errors),
    )

    return result


async def _classify_adaptations(
    session,
    classifier: AdaptationClassifier,
    result: ComputeEvolutionResult,
    dry_run: bool,
) -> None:
    """Find and classify unclassified adaptations."""
    query = select(Adaptation).where(
        Adaptation.source != "claude",
    )
    db_result = await session.execute(query)
    adaptations = list(db_result.scalars().all())

    logger.info("Found %d unclassified adaptations", len(adaptations))

    for adaptation in adaptations:
        try:
            if not dry_run:
                await classifier.classify(adaptation)
            result.adaptations_classified += 1
        except (AdaptationClassifierError, ClaudeError) as e:
            logger.warning(
                "Failed to classify adaptation %s: %s",
                adaptation.id,
                e,
                exc_info=True,
            )
            result.errors.append(
                f"Classification failed for adaptation {adaptation.id}: {e}"
            )

    if not dry_run and adaptations:
        await session.commit()


async def _generate_meta_contexts(
    session,
    classifier: AdaptationClassifier,
    result: ComputeEvolutionResult,
    dry_run: bool,
) -> None:
    """Generate meta context for snapshots that don't have one."""
    query = select(ArchetypeEvolutionSnapshot).where(
        ArchetypeEvolutionSnapshot.meta_context.is_(None),
    )
    db_result = await session.execute(query)
    snapshots = list(db_result.scalars().all())

    logger.info("Found %d snapshots missing meta context", len(snapshots))

    for snapshot in snapshots:
        try:
            if not dry_run:
                context = await classifier.classify_and_contextualize(snapshot.id)
                if context:
                    result.contexts_generated += 1
            else:
                result.contexts_generated += 1
        except (AdaptationClassifierError, ClaudeError) as e:
            logger.warning(
                "Failed to generate context for snapshot %s: %s",
                snapshot.id,
                e,
                exc_info=True,
            )
            result.errors.append(
                f"Context generation failed for snapshot {snapshot.id}: {e}"
            )


async def _generate_predictions(
    session,
    engine: PredictionEngine,
    result: ComputeEvolutionResult,
    dry_run: bool,
) -> None:
    """Generate predictions for upcoming major tournaments."""
    today = date_type.today()
    query = select(Tournament).where(
        Tournament.date > today,
        Tournament.tier.in_(["major", "premier"]),
    )
    db_result = await session.execute(query)
    tournaments = list(db_result.scalars().all())

    if not tournaments:
        logger.info("No upcoming major tournaments for predictions")
        return

    # Get active archetypes (those with recent snapshots)
    archetype_query = (
        select(ArchetypeEvolutionSnapshot.archetype)
        .distinct()
        .order_by(ArchetypeEvolutionSnapshot.archetype)
    )
    arch_result = await session.execute(archetype_query)
    archetypes = [row[0] for row in arch_result.all()]

    if not archetypes:
        logger.info("No archetypes found for predictions")
        return

    # Batch-load existing predictions to avoid N+1 queries
    tournament_ids = [t.id for t in tournaments]
    existing_query = select(
        ArchetypePrediction.archetype_id,
        ArchetypePrediction.target_tournament_id,
    ).where(ArchetypePrediction.target_tournament_id.in_(tournament_ids))
    existing_result = await session.execute(existing_query)
    existing_predictions = {
        (row[0], row[1]) for row in existing_result.all()
    }

    logger.info(
        "Generating predictions for %d tournaments x %d archetypes "
        "(%d existing predictions found)",
        len(tournaments),
        len(archetypes),
        len(existing_predictions),
    )

    for tournament in tournaments:
        for archetype in archetypes:
            if (archetype, tournament.id) in existing_predictions:
                continue

            try:
                if not dry_run:
                    prediction = await engine.predict(archetype, tournament.id)
                    session.add(prediction)
                result.predictions_generated += 1
            except (PredictionEngineError, ClaudeError) as e:
                logger.warning(
                    "Failed to predict %s at tournament %s: %s",
                    archetype,
                    tournament.id,
                    e,
                    exc_info=True,
                )
                result.errors.append(
                    f"Prediction failed for {archetype} at {tournament.id}: {e}"
                )

    if not dry_run:
        await session.commit()


async def _generate_articles(
    session,
    generator: EvolutionArticleGenerator,
    result: ComputeEvolutionResult,
    dry_run: bool,
) -> None:
    """Generate evolution articles for archetypes with sufficient data."""
    archetype_query = (
        select(
            ArchetypeEvolutionSnapshot.archetype,
            func.count(ArchetypeEvolutionSnapshot.id).label("count"),
        )
        .group_by(ArchetypeEvolutionSnapshot.archetype)
        .having(func.count(ArchetypeEvolutionSnapshot.id) >= 3)
    )
    arch_result = await session.execute(archetype_query)
    archetypes = [row[0] for row in arch_result.all()]

    logger.info(
        "Found %d archetypes eligible for article generation",
        len(archetypes),
    )

    for archetype in archetypes:
        try:
            if not dry_run:
                article = await generator.generate_article(archetype)
                session.add(article)

                # Link snapshots
                snapshot_query = (
                    select(ArchetypeEvolutionSnapshot.id)
                    .join(
                        Tournament,
                        ArchetypeEvolutionSnapshot.tournament_id == Tournament.id,
                    )
                    .where(ArchetypeEvolutionSnapshot.archetype == archetype)
                    .order_by(Tournament.date.desc())
                    .limit(6)
                )
                snap_result = await session.execute(snapshot_query)
                snapshot_ids = [row[0] for row in snap_result.all()]
                links = await generator.link_snapshots(article, snapshot_ids)
                for link in links:
                    session.add(link)

            result.articles_generated += 1
        except (ArticleGeneratorError, ClaudeError) as e:
            logger.warning(
                "Failed to generate article for %s: %s",
                archetype,
                e,
                exc_info=True,
            )
            result.errors.append(f"Article generation failed for {archetype}: {e}")

    if not dry_run:
        await session.commit()
