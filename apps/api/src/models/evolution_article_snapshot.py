"""EvolutionArticleSnapshot join table linking articles to snapshots."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
    from src.models.evolution_article import EvolutionArticle


class EvolutionArticleSnapshot(Base):
    """Join table between EvolutionArticle and ArchetypeEvolutionSnapshot.

    Uses a composite primary key of (article_id, snapshot_id) with an
    ordering position for display.
    """

    __tablename__ = "evolution_article_snapshots"

    # Composite primary key
    article_id: Mapped[UUID] = mapped_column(
        ForeignKey("evolution_articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("archetype_evolution_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Display ordering
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    article: Mapped["EvolutionArticle"] = relationship(
        "EvolutionArticle", back_populates="article_snapshots"
    )
    snapshot: Mapped["ArchetypeEvolutionSnapshot"] = relationship(
        "ArchetypeEvolutionSnapshot", back_populates="article_snapshots"
    )
