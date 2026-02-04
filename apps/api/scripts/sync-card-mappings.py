#!/usr/bin/env python
"""CLI script to sync JP-to-EN card ID mappings from Limitless.

Usage:
    uv run scripts/sync-card-mappings.py --help
    uv run scripts/sync-card-mappings.py                    # Sync all JP sets
    uv run scripts/sync-card-mappings.py --recent           # Sync only recent sets
    uv run scripts/sync-card-mappings.py --sets SV7 SV7a    # Sync specific sets
    uv run scripts/sync-card-mappings.py --dry-run          # Preview without changes
"""

import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.sync_card_mappings import (
    sync_all_card_mappings,
    sync_recent_jp_sets,
)

app = typer.Typer(
    name="sync-card-mappings",
    help="Sync JP-to-EN card ID mappings from Limitless.",
    no_args_is_help=False,
)
console = Console()


def setup_logging(verbose: bool) -> None:
    """Configure logging with rich handler.

    Args:
        verbose: Enable verbose (DEBUG) logging.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def sync(
    recent: bool = typer.Option(
        False,
        "--recent",
        "-r",
        help="Only sync recent JP sets (default: 5 most recent).",
    ),
    lookback: int = typer.Option(
        5,
        "--lookback",
        "-l",
        help="Number of recent sets to sync (with --recent).",
    ),
    sets: list[str] = typer.Option(  # noqa: B008
        None,
        "--sets",
        "-s",
        help="Specific JP set codes to sync (e.g., SV7 SV7a).",
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
    """Sync JP-to-EN card ID mappings from Limitless.

    This scrapes Limitless card detail pages to build a mapping between
    Japanese card IDs (e.g., SV7-18) and English card IDs (e.g., SCR-28).

    The mapping is used by the archetype detector to properly identify
    deck archetypes in Japanese tournament decklists.

    By default, syncs all available JP sets. Use --recent to only sync
    the most recent sets, or --sets to specify exact sets.
    """
    setup_logging(verbose)

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] - No changes will be committed.\n")

    if sets and recent:
        console.print(
            "[red]Error:[/red] Cannot use --sets and --recent together."
        )
        raise typer.Exit(1)

    asyncio.run(_run_sync(sets, recent, lookback, dry_run))


async def _run_sync(
    sets: list[str] | None,
    recent: bool,
    lookback: int,
    dry_run: bool,
) -> None:
    """Run the sync operation.

    Args:
        sets: Specific JP set codes to sync, or None for all/recent.
        recent: Whether to only sync recent sets.
        lookback: Number of recent sets to sync.
        dry_run: Whether to actually commit changes.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        if sets:
            task = progress.add_task(
                f"Syncing {len(sets)} specified JP sets...", total=None
            )
            result = await sync_all_card_mappings(jp_sets=sets, dry_run=dry_run)
        elif recent:
            task = progress.add_task(
                f"Syncing {lookback} recent JP sets...", total=None
            )
            result = await sync_recent_jp_sets(lookback_sets=lookback, dry_run=dry_run)
        else:
            task = progress.add_task("Syncing all JP sets...", total=None)
            result = await sync_all_card_mappings(dry_run=dry_run)

        progress.update(task, completed=True)

    console.print()
    if result.success:
        console.print("[green]Sync complete![/green]")
    else:
        console.print("[yellow]Sync completed with errors.[/yellow]")

    console.print("\n[bold]Results:[/bold]")
    console.print(f"  Sets processed:    {result.sets_processed}")
    console.print(f"  Mappings found:    {result.mappings_found}")
    console.print(f"  Mappings inserted: {result.mappings_inserted}")
    console.print(f"  Mappings updated:  {result.mappings_updated}")

    if result.errors:
        console.print(f"\n[red]Errors: {len(result.errors)}[/red]")
        for error in result.errors[:5]:
            console.print(f"  - {error}")
        if len(result.errors) > 5:
            console.print(f"  ... and {len(result.errors) - 5} more")
        raise typer.Exit(1)


@app.command("show")
def show_mappings(
    set_id: str = typer.Argument(
        None,
        help="JP set code to show mappings for (e.g., SV7).",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of mappings to show.",
    ),
) -> None:
    """Show existing card ID mappings from the database."""
    asyncio.run(_show_mappings(set_id, limit))


async def _show_mappings(set_id: str | None, limit: int) -> None:
    """Display existing card mappings.

    Args:
        set_id: Optional JP set code to filter by.
        limit: Max mappings to display.
    """
    from sqlalchemy import select

    from src.db.database import async_session_factory
    from src.models import CardIdMapping

    async with async_session_factory() as session:
        query = select(CardIdMapping).limit(limit)
        if set_id:
            query = query.where(CardIdMapping.jp_set_id == set_id.upper())
        query = query.order_by(CardIdMapping.jp_card_id)

        result = await session.execute(query)
        mappings = result.scalars().all()

    if not mappings:
        if set_id:
            console.print(f"[yellow]No mappings found for set {set_id}[/yellow]")
        else:
            console.print("[yellow]No card ID mappings in database.[/yellow]")
            console.print("Run [bold]sync-card-mappings.py[/bold] to populate.")
        return

    table = Table(title=f"Card ID Mappings{f' ({set_id})' if set_id else ''}")
    table.add_column("JP Card ID", style="cyan")
    table.add_column("EN Card ID", style="green")
    table.add_column("Card Name", style="white")
    table.add_column("JP Set", style="magenta")
    table.add_column("EN Set", style="magenta")

    for m in mappings:
        table.add_row(
            m.jp_card_id,
            m.en_card_id,
            m.card_name_en or "",
            m.jp_set_id or "",
            m.en_set_id or "",
        )

    console.print(table)
    console.print(f"\nShowing {len(mappings)} of {limit} max mappings.")


@app.command("stats")
def show_stats() -> None:
    """Show statistics about card ID mappings."""
    asyncio.run(_show_stats())


async def _show_stats() -> None:
    """Display mapping statistics."""
    from sqlalchemy import distinct, func, select

    from src.db.database import async_session_factory
    from src.models import CardIdMapping

    async with async_session_factory() as session:
        total = await session.scalar(select(func.count(CardIdMapping.id)))
        jp_sets = await session.scalar(
            select(func.count(distinct(CardIdMapping.jp_set_id)))
        )
        en_sets = await session.scalar(
            select(func.count(distinct(CardIdMapping.en_set_id)))
        )

        set_counts_query = (
            select(
                CardIdMapping.jp_set_id,
                func.count(CardIdMapping.id).label("count"),
            )
            .group_by(CardIdMapping.jp_set_id)
            .order_by(func.count(CardIdMapping.id).desc())
            .limit(10)
        )
        set_counts = await session.execute(set_counts_query)

    console.print("\n[bold]Card ID Mapping Statistics[/bold]")
    console.print(f"  Total mappings:    {total or 0}")
    console.print(f"  JP sets covered:   {jp_sets or 0}")
    console.print(f"  EN sets covered:   {en_sets or 0}")

    if total and total > 0:
        console.print("\n[bold]Top JP Sets by Mapping Count:[/bold]")
        table = Table()
        table.add_column("JP Set", style="cyan")
        table.add_column("Mappings", justify="right")

        for row in set_counts:
            table.add_row(row.jp_set_id or "Unknown", str(row.count))

        console.print(table)
    else:
        console.print("\n[yellow]No mappings yet.[/yellow]")
        console.print("Run [bold]sync-card-mappings.py[/bold] to populate.")


if __name__ == "__main__":
    app()
