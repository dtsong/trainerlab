"""SQLAlchemy models."""

from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.card import Card
from src.models.deck import Deck
from src.models.evolution_article import EvolutionArticle
from src.models.evolution_article_snapshot import EvolutionArticleSnapshot
from src.models.format_config import FormatConfig
from src.models.jp_card_innovation import JPCardInnovation
from src.models.jp_new_archetype import JPNewArchetype
from src.models.jp_set_impact import JPSetImpact
from src.models.lab_note import LabNote
from src.models.lab_note_revision import LabNoteRevision
from src.models.meta_snapshot import MetaSnapshot
from src.models.prediction import Prediction
from src.models.rotation_impact import RotationImpact
from src.models.set import Set
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.models.user import User
from src.models.waitlist import WaitlistEntry

__all__ = [
    "Adaptation",
    "ArchetypeEvolutionSnapshot",
    "ArchetypePrediction",
    "Card",
    "Deck",
    "EvolutionArticle",
    "EvolutionArticleSnapshot",
    "FormatConfig",
    "JPCardInnovation",
    "JPNewArchetype",
    "JPSetImpact",
    "LabNote",
    "LabNoteRevision",
    "MetaSnapshot",
    "Prediction",
    "RotationImpact",
    "Set",
    "Tournament",
    "TournamentPlacement",
    "User",
    "WaitlistEntry",
]
