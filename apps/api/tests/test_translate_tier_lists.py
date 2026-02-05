"""Tests for translate_tier_lists pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.pokecabook import PokecabookTierEntry, PokecabookTierList
from src.clients.pokekameshi import PokekameshiTierEntry, PokekameshiTierTable
from src.pipelines.translate_tier_lists import (
    TranslateTierListsResult,
    _format_combined_tier_lists,
    translate_tier_lists,
)


class TestTranslateTierListsResult:
    """Tests for the result dataclass."""

    def test_success_when_no_errors(self) -> None:
        """Should report success when errors list is empty."""
        result = TranslateTierListsResult()
        assert result.success is True

    def test_failure_when_errors_present(self) -> None:
        """Should report failure when errors exist."""
        result = TranslateTierListsResult(errors=["something went wrong"])
        assert result.success is False


class TestFormatCombinedTierLists:
    """Tests for _format_combined_tier_lists covering lines 143-179."""

    def test_formats_pokecabook_data(self) -> None:
        """Should format Pokecabook entries with tier headers and usage rates."""
        pokecabook = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[
                PokecabookTierEntry(
                    archetype_name="リザードンex", tier="S", usage_rate=0.15
                ),
                PokecabookTierEntry(
                    archetype_name="サーナイトex", tier="S", usage_rate=0.12
                ),
                PokecabookTierEntry(
                    archetype_name="ルギアVSTAR", tier="A", usage_rate=0.08
                ),
            ],
        )

        result = _format_combined_tier_lists(pokecabook, None)

        assert "【Pokecabook Tier List】" in result
        assert "S:" in result
        assert "A:" in result
        assert "リザードンex" in result
        assert "15.0%" in result
        assert "12.0%" in result

    def test_formats_pokecabook_entry_without_usage_rate(self) -> None:
        """Should format entries without usage rate (no parenthetical)."""
        pokecabook = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[
                PokecabookTierEntry(
                    archetype_name="テストデッキ", tier="B", usage_rate=None
                ),
            ],
        )

        result = _format_combined_tier_lists(pokecabook, None)
        assert "テストデッキ" in result
        assert "%" not in result.split("テストデッキ")[1].split("\n")[0]

    def test_formats_pokekameshi_data(self) -> None:
        """Should format Pokekameshi entries with stats."""
        pokekameshi = PokekameshiTierTable(
            date=date(2026, 2, 5),
            environment_name="SV6環境",
            entries=[
                PokekameshiTierEntry(
                    archetype_name="リザードンex",
                    tier="Tier1",
                    share_rate=0.15,
                    csp_points=120,
                    deck_power=8.5,
                ),
            ],
        )

        result = _format_combined_tier_lists(None, pokekameshi)

        assert "【Pokekameshi Tier Table】" in result
        assert "環境: SV6環境" in result
        assert "Tier1:" in result
        assert "15.0%" in result
        assert "CSP:120" in result
        assert "Power:8.5" in result

    def test_formats_pokekameshi_without_environment(self) -> None:
        """Should handle None environment_name gracefully."""
        pokekameshi = PokekameshiTierTable(
            date=date(2026, 2, 5),
            environment_name=None,
            entries=[
                PokekameshiTierEntry(archetype_name="テスト", tier="Tier2"),
            ],
        )

        result = _format_combined_tier_lists(None, pokekameshi)
        assert "環境:" not in result
        assert "テスト" in result

    def test_formats_pokekameshi_partial_stats(self) -> None:
        """Should handle entries with only some stats present."""
        pokekameshi = PokekameshiTierTable(
            date=date(2026, 2, 5),
            entries=[
                PokekameshiTierEntry(
                    archetype_name="DeckA",
                    tier="Tier1",
                    share_rate=0.10,
                    csp_points=None,
                    deck_power=None,
                ),
                PokekameshiTierEntry(
                    archetype_name="DeckB",
                    tier="Tier1",
                    share_rate=None,
                    csp_points=80,
                    deck_power=None,
                ),
                PokekameshiTierEntry(
                    archetype_name="DeckC",
                    tier="Tier1",
                    share_rate=None,
                    csp_points=None,
                    deck_power=7.2,
                ),
                PokekameshiTierEntry(
                    archetype_name="DeckD",
                    tier="Tier1",
                    share_rate=None,
                    csp_points=None,
                    deck_power=None,
                ),
            ],
        )

        result = _format_combined_tier_lists(None, pokekameshi)
        assert "10.0%" in result
        assert "CSP:80" in result
        assert "Power:7.2" in result
        # DeckD has no stats, should not have parenthetical
        deck_d_line = [line for line in result.split("\n") if "DeckD" in line][0]
        assert "(" not in deck_d_line

    def test_formats_both_sources(self) -> None:
        """Should include both Pokecabook and Pokekameshi sections."""
        pokecabook = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[PokecabookTierEntry(archetype_name="DeckA", tier="S")],
        )
        pokekameshi = PokekameshiTierTable(
            date=date(2026, 2, 5),
            entries=[PokekameshiTierEntry(archetype_name="DeckB", tier="Tier1")],
        )

        result = _format_combined_tier_lists(pokecabook, pokekameshi)
        assert "【Pokecabook Tier List】" in result
        assert "【Pokekameshi Tier Table】" in result

    def test_handles_both_none(self) -> None:
        """Should handle both sources being None."""
        result = _format_combined_tier_lists(None, None)
        assert "JP Meta Tier Lists" in result


class TestTranslateTierListsPipeline:
    """Tests for translate_tier_lists function covering error paths."""

    @pytest.mark.asyncio
    async def test_pokecabook_error_records_warning(self) -> None:
        """Should record error when Pokecabook fetch fails (lines 64-67)."""
        from src.clients.pokecabook import PokecabookError
        from src.clients.pokekameshi import PokekameshiError

        with (
            patch(
                "src.pipelines.translate_tier_lists.PokecabookClient"
            ) as mock_pcb_cls,
            patch(
                "src.pipelines.translate_tier_lists.PokekameshiClient"
            ) as mock_pkm_cls,
        ):
            # Pokecabook fails
            mock_pcb = AsyncMock()
            mock_pcb.fetch_tier_list.side_effect = PokecabookError("Network error")
            mock_pcb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pcb)
            mock_pcb_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            # Pokekameshi also fails
            mock_pkm = AsyncMock()
            mock_pkm.fetch_tier_tables.side_effect = PokekameshiError("Timeout")
            mock_pkm_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pkm)
            mock_pkm_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await translate_tier_lists(dry_run=False)

            assert result.success is False
            assert len(result.errors) >= 2
            assert "No tier list data could be fetched" in result.errors[-1]

    @pytest.mark.asyncio
    async def test_pokekameshi_error_alone(self) -> None:
        """Should record Pokekameshi error while Pokecabook succeeds (lines 72-74)."""
        from src.clients.pokekameshi import PokekameshiError

        pokecabook_data = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[PokecabookTierEntry(archetype_name="DeckA", tier="S")],
        )

        with (
            patch(
                "src.pipelines.translate_tier_lists.PokecabookClient"
            ) as mock_pcb_cls,
            patch(
                "src.pipelines.translate_tier_lists.PokekameshiClient"
            ) as mock_pkm_cls,
            patch("src.pipelines.translate_tier_lists.ClaudeClient") as mock_claude_cls,
            patch(
                "src.pipelines.translate_tier_lists.async_session_factory"
            ) as mock_sf,
        ):
            # Pokecabook succeeds
            mock_pcb = AsyncMock()
            mock_pcb.fetch_tier_list.return_value = pokecabook_data
            mock_pcb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pcb)
            mock_pcb_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            # Pokekameshi fails
            mock_pkm = AsyncMock()
            mock_pkm.fetch_tier_tables.side_effect = PokekameshiError("Error")
            mock_pkm_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pkm)
            mock_pkm_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            # Claude + session for translation
            mock_claude = AsyncMock()
            mock_claude_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_claude
            )
            mock_claude_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock TranslationService.translate_article
            with patch(
                "src.pipelines.translate_tier_lists.TranslationService"
            ) as mock_ts_cls:
                mock_ts = AsyncMock()
                mock_ts_cls.return_value = mock_ts

                result = await translate_tier_lists(dry_run=False)

            assert result.pokecabook_entries == 1
            assert any("Pokekameshi" in e for e in result.errors)
            assert result.translations_saved == 1

    @pytest.mark.asyncio
    async def test_translation_error_recorded(self) -> None:
        """Should record translation error (lines 122-125)."""
        pokecabook_data = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[PokecabookTierEntry(archetype_name="DeckA", tier="S")],
        )

        with (
            patch(
                "src.pipelines.translate_tier_lists.PokecabookClient"
            ) as mock_pcb_cls,
            patch(
                "src.pipelines.translate_tier_lists.PokekameshiClient"
            ) as mock_pkm_cls,
            patch("src.pipelines.translate_tier_lists.ClaudeClient") as mock_claude_cls,
            patch("src.pipelines.translate_tier_lists.async_session_factory"),
        ):
            mock_pcb = AsyncMock()
            mock_pcb.fetch_tier_list.return_value = pokecabook_data
            mock_pcb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pcb)
            mock_pcb_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_pkm = AsyncMock()
            mock_pkm.fetch_tier_tables.return_value = PokekameshiTierTable(
                date=date(2026, 2, 5), entries=[]
            )
            mock_pkm_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pkm)
            mock_pkm_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_claude_cls.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("API error")
            )
            mock_claude_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await translate_tier_lists(dry_run=False)

            assert any("Error translating" in e for e in result.errors)
            assert result.translations_saved == 0

    @pytest.mark.asyncio
    async def test_dry_run_path(self) -> None:
        """Should translate but not persist in dry_run mode (lines 97-108)."""
        pokecabook_data = PokecabookTierList(
            date=date(2026, 2, 5),
            entries=[PokecabookTierEntry(archetype_name="DeckA", tier="S")],
        )

        with (
            patch(
                "src.pipelines.translate_tier_lists.PokecabookClient"
            ) as mock_pcb_cls,
            patch(
                "src.pipelines.translate_tier_lists.PokekameshiClient"
            ) as mock_pkm_cls,
            patch("src.pipelines.translate_tier_lists.ClaudeClient") as mock_claude_cls,
            patch(
                "src.pipelines.translate_tier_lists.async_session_factory"
            ) as mock_sf,
        ):
            mock_pcb = AsyncMock()
            mock_pcb.fetch_tier_list.return_value = pokecabook_data
            mock_pcb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pcb)
            mock_pcb_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_pkm = AsyncMock()
            mock_pkm.fetch_tier_tables.return_value = PokekameshiTierTable(
                date=date(2026, 2, 5), entries=[]
            )
            mock_pkm_cls.return_value.__aenter__ = AsyncMock(return_value=mock_pkm)
            mock_pkm_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_claude = AsyncMock()
            mock_claude_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_claude
            )
            mock_claude_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "src.pipelines.translate_tier_lists.TranslationService"
            ) as mock_ts_cls:
                mock_ts = AsyncMock()
                mock_translation = MagicMock()
                mock_translation.layer_used = "cache"
                mock_translation.confidence = 0.95
                mock_ts.translate.return_value = mock_translation
                mock_ts_cls.return_value = mock_ts

                result = await translate_tier_lists(dry_run=True)

            assert result.translations_saved == 1
            assert result.pokecabook_entries == 1
