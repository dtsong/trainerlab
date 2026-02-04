"""Data module containing static data and mappings."""

from src.data.signature_cards import SIGNATURE_CARDS
from src.data.tcg_glossary import (
    TCG_GLOSSARY,
    GlossaryEntry,
    get_claude_glossary,
    get_terms_by_category,
    lookup_term,
)

__all__ = [
    "GlossaryEntry",
    "SIGNATURE_CARDS",
    "TCG_GLOSSARY",
    "get_claude_glossary",
    "get_terms_by_category",
    "lookup_term",
]
