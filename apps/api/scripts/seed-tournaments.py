#!/usr/bin/env python
"""CLI script to seed tournament data from JSON fixtures.

Usage:
    uv run scripts/seed-tournaments.py --help
    uv run scripts/seed-tournaments.py                    # Seed all tournaments
    uv run scripts/seed-tournaments.py --dry-run         # Preview without changes
    uv run scripts/seed-tournaments.py --clear           # Clear and re-seed
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError
from sqlalchemy import delete, select

from src.db.database import async_session_factory
from src.fixtures.tournaments import TournamentFixture, normalize_archetype
from src.models import Tournament, TournamentPlacement

app = typer.Typer(
    name="seed-tournaments",
    help="Seed tournament data from JSON fixtures.",
    no_args_is_help=False,
)
console = Console()

# Path to fixtures
FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "tournaments.json"

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Configure logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def load_fixtures() -> list[TournamentFixture]:
    """Load tournament fixtures from JSON file.

    Returns:
        List of validated TournamentFixture objects.

    Raises:
        typer.Exit: If file not found, invalid JSON, or validation fails.
    """
    if not FIXTURES_PATH.exists():
        console.print(f"[red]Error:[/red] Fixtures file not found: {FIXTURES_PATH}")
        raise typer.Exit(1)

    try:
        with open(FIXTURES_PATH) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in fixtures file: {e}")
        raise typer.Exit(1) from None
    except OSError as e:
        console.print(f"[red]Error:[/red] Failed to read fixtures file: {e}")
        raise typer.Exit(1) from None

    tournaments = []
    for i, item in enumerate(data.get("tournaments", [])):
        try:
            tournament = TournamentFixture.model_validate(item)
            tournaments.append(tournament)
        except ValidationError as e:
            tournament_name = item.get("name", f"index {i}")
            console.print(
                f"[red]Error:[/red] Invalid tournament data for '{tournament_name}':"
            )
            console.print(f"  {e}")
            raise typer.Exit(1) from None

    return tournaments


async def clear_tournaments() -> int:
    """Clear all tournament data from database.

    Returns:
        Number of tournaments deleted.
    """
    async with async_session_factory() as session:
        # Count existing
        result = await session.execute(select(Tournament))
        count = len(result.scalars().all())

        # Delete all (cascades to placements)
        await session.execute(delete(Tournament))
        await session.commit()

        return count


async def seed_tournament(fixture: TournamentFixture, dry_run: bool = False) -> bool:
    """Seed a single tournament from fixture.

    Args:
        fixture: Tournament fixture data.
        dry_run: If True, don't commit changes.

    Returns:
        True if tournament was created, False if it already exists.
    """
    async with async_session_factory() as session:
        # Check if tournament already exists (by name and date)
        result = await session.execute(
            select(Tournament).where(
                Tournament.name == fixture.name,
                Tournament.date == fixture.date,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.debug("Tournament already exists: %s", fixture.name)
            return False

        # Create tournament
        tournament_id = uuid4()
        tournament = Tournament(
            id=tournament_id,
            name=fixture.name,
            date=fixture.date,
            region=fixture.region,
            country=fixture.country,
            format=fixture.game_format,
            best_of=fixture.best_of,
            participant_count=fixture.participant_count,
            source=fixture.source,
            source_url=fixture.source_url,
        )

        session.add(tournament)

        # Create placements
        for placement_data in fixture.placements:
            archetype = normalize_archetype(placement_data.archetype)
            placement = TournamentPlacement(
                id=uuid4(),
                tournament_id=tournament_id,
                placement=placement_data.placement,
                player_name=placement_data.player_name,
                archetype=archetype,
                decklist=placement_data.decklist,
                decklist_source=placement_data.decklist_source,
            )
            session.add(placement)

        if not dry_run:
            await session.commit()
        else:
            await session.rollback()

        return True


@app.command()
def seed(
    clear: bool = typer.Option(
        False,
        "--clear",
        "-c",
        help="Clear existing tournaments before seeding.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without committing to database.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging.",
    ),
) -> None:
    """Seed tournament data from JSON fixtures."""
    setup_logging(verbose)

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] - No changes will be committed.\n")

    # Load fixtures
    console.print(f"Loading fixtures from {FIXTURES_PATH}...")
    fixtures = load_fixtures()
    console.print(f"Found {len(fixtures)} tournaments in fixtures.\n")

    # Clear if requested
    if clear and not dry_run:
        console.print("[yellow]Clearing existing tournaments...[/yellow]")
        deleted = asyncio.run(clear_tournaments())
        console.print(f"Deleted {deleted} tournaments.\n")

    # Seed tournaments
    created = 0
    skipped = 0
    failed = 0

    for fixture in fixtures:
        try:
            was_created = asyncio.run(seed_tournament(fixture, dry_run))
            if was_created:
                created += 1
                logger.info("Created: %s (%s)", fixture.name, fixture.region)
            else:
                skipped += 1
                logger.info("Skipped (exists): %s", fixture.name)
        except Exception as e:
            failed += 1
            console.print(f"[red]Error seeding '{fixture.name}':[/red] {e}")
            logger.error("Failed to seed %s: %s", fixture.name, str(e))

    # Summary
    console.print()
    if failed > 0:
        console.print("[yellow]Seed completed with errors.[/yellow]")
    else:
        console.print("[green]Seed complete![/green]")
    console.print(f"  Created: {created}")
    console.print(f"  Skipped: {skipped}")
    if failed > 0:
        console.print(f"  [red]Failed: {failed}[/red]")

    # Show preview table
    if fixtures:
        table = Table(title="Seeded Tournaments")
        table.add_column("Name", style="cyan")
        table.add_column("Region", style="magenta")
        table.add_column("Date")
        table.add_column("Format")
        table.add_column("BO")
        table.add_column("Placements", justify="right")

        for fixture in fixtures:
            table.add_row(
                fixture.name[:30],
                fixture.region,
                str(fixture.date),
                fixture.game_format,
                str(fixture.best_of),
                str(len(fixture.placements)),
            )

        console.print()
        console.print(table)


if __name__ == "__main__":
    app()
