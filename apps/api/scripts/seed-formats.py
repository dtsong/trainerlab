#!/usr/bin/env python
"""CLI script to seed format configuration data from JSON fixtures.

Usage:
    uv run scripts/seed-formats.py --help
    uv run scripts/seed-formats.py                    # Seed all formats
    uv run scripts/seed-formats.py --dry-run          # Preview without changes
    uv run scripts/seed-formats.py --clear            # Clear and re-seed
"""

import asyncio
import json
import logging
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db.database import async_session_factory
from src.models import FormatConfig

app = typer.Typer(
    name="seed-formats",
    help="Seed format configuration data from JSON fixtures.",
    no_args_is_help=False,
)
console = Console()

# Path to fixtures
FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "formats.json"

logger = logging.getLogger(__name__)


class FormatFixture(BaseModel):
    """Pydantic model for format fixture validation."""

    name: str
    display_name: str
    legal_sets: list[str]
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    is_upcoming: bool = False
    rotation_details: dict | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is lowercase."""
        return v.lower()


def setup_logging(verbose: bool) -> None:
    """Configure logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def load_fixtures() -> list[FormatFixture]:
    """Load format fixtures from JSON file.

    Returns:
        List of validated FormatFixture objects.

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

    formats = []
    for i, item in enumerate(data.get("formats", [])):
        try:
            format_config = FormatFixture.model_validate(item)
            formats.append(format_config)
        except Exception as e:
            format_name = item.get("name", f"index {i}")
            console.print(f"[red]Error:[/red] Invalid format data for '{format_name}':")
            console.print(f"  {e}")
            raise typer.Exit(1) from None

    return formats


async def clear_formats() -> int:
    """Clear all format data from database.

    Returns:
        Number of formats deleted.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(select(FormatConfig))
            count = len(result.scalars().all())

            await session.execute(delete(FormatConfig))
            await session.commit()

            return count
    except SQLAlchemyError:
        logger.error("Failed to clear formats", exc_info=True)
        raise


async def seed_format(fixture: FormatFixture, dry_run: bool = False) -> bool:
    """Seed a single format from fixture.

    Args:
        fixture: Format fixture data.
        dry_run: If True, don't commit changes.

    Returns:
        True if format was created, False if it already exists.
    """
    async with async_session_factory() as session:
        # Check if format already exists (by name)
        result = await session.execute(
            select(FormatConfig).where(FormatConfig.name == fixture.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.debug("Format already exists: %s", fixture.name)
            return False

        # Create format
        format_config = FormatConfig(
            id=uuid4(),
            name=fixture.name,
            display_name=fixture.display_name,
            legal_sets=fixture.legal_sets,
            start_date=fixture.start_date,
            end_date=fixture.end_date,
            is_current=fixture.is_current,
            is_upcoming=fixture.is_upcoming,
            rotation_details=fixture.rotation_details,
        )

        session.add(format_config)

        if not dry_run:
            await session.commit()
        else:
            await session.rollback()

        return True


async def run_seed(
    fixtures: list[FormatFixture],
    clear: bool,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Run the seeding process in a single event loop.

    Returns:
        Tuple of (created, skipped, failed) counts.
    """
    created = 0
    skipped = 0
    failed = 0

    # Clear if requested
    if clear and not dry_run:
        console.print("[yellow]Clearing existing formats...[/yellow]")
        try:
            deleted = await clear_formats()
            console.print(f"Deleted {deleted} formats.\n")
        except SQLAlchemyError as e:
            console.print(f"[red]Error:[/red] Failed to clear formats: {e}")
            console.print("Check database connection and try again.")
            raise typer.Exit(1) from None

    # Seed formats
    for fixture in fixtures:
        try:
            was_created = await seed_format(fixture, dry_run)
            if was_created:
                created += 1
                logger.info("Created: %s", fixture.display_name)
            else:
                skipped += 1
                logger.info("Skipped (exists): %s", fixture.name)
        except IntegrityError as e:
            console.print(
                f"[red]Database integrity error for '{fixture.name}':[/red] {e}"
            )
            logger.error(
                "Integrity error seeding %s: %s",
                fixture.name,
                str(e),
            )
            console.print("[red]Aborting seed due to integrity error.[/red]")
            raise typer.Exit(1) from None
        except SQLAlchemyError as e:
            failed += 1
            console.print(f"[red]Database error seeding '{fixture.name}':[/red] {e}")
            logger.error("Database error seeding %s: %s", fixture.name, str(e))
        except Exception as e:
            failed += 1
            error_type = type(e).__name__
            console.print(
                f"[red]Unexpected error seeding '{fixture.name}':[/red] "
                f"{error_type}: {e}"
            )
            logger.error(
                "Unexpected error seeding %s: %s", fixture.name, str(e), exc_info=True
            )

    return created, skipped, failed


@app.command()
def seed(
    clear: bool = typer.Option(
        False,
        "--clear",
        "-c",
        help="Clear existing formats before seeding.",
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
    """Seed format configuration data from JSON fixtures."""
    setup_logging(verbose)

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] - No changes will be committed.\n")

    # Load fixtures
    console.print(f"Loading fixtures from {FIXTURES_PATH}...")
    fixtures = load_fixtures()
    console.print(f"Found {len(fixtures)} formats in fixtures.\n")

    # Run all async operations in a single event loop
    created, skipped, failed = asyncio.run(run_seed(fixtures, clear, dry_run))

    # Summary
    console.print()
    if failed > 0:
        console.print("[yellow]Seed completed with errors.[/yellow]")
        console.print(f"  Created: {created}")
        console.print(f"  Skipped: {skipped}")
        console.print(f"  [red]Failed: {failed}[/red]")
        raise typer.Exit(1)
    else:
        console.print("[green]Seed complete![/green]")
        console.print(f"  Created: {created}")
        console.print(f"  Skipped: {skipped}")

    # Show preview table
    if fixtures:
        table = Table(title="Format Configurations")
        table.add_column("Name", style="cyan")
        table.add_column("Display", style="magenta")
        table.add_column("Sets", justify="right")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Current")
        table.add_column("Upcoming")

        for fixture in fixtures:
            table.add_row(
                fixture.name,
                fixture.display_name,
                str(len(fixture.legal_sets)),
                str(fixture.start_date) if fixture.start_date else "-",
                str(fixture.end_date) if fixture.end_date else "-",
                "✓" if fixture.is_current else "",
                "✓" if fixture.is_upcoming else "",
            )

        console.print()
        console.print(table)


if __name__ == "__main__":
    app()
