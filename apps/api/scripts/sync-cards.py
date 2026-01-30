#!/usr/bin/env python
"""CLI script to sync card data from TCGdex.

Usage:
    uv run scripts/sync-cards.py --help
    uv run scripts/sync-cards.py                    # Sync all (English + Japanese)
    uv run scripts/sync-cards.py --english-only    # Sync English cards only
    uv run scripts/sync-cards.py --japanese-only   # Sync Japanese names only
    uv run scripts/sync-cards.py --dry-run         # Preview without changes
"""

import asyncio
import logging
import sys
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.sync_cards import sync_all, sync_english_cards, sync_japanese_names

app = typer.Typer(
    name="sync-cards",
    help="Sync Pokemon TCG card data from TCGdex.",
    no_args_is_help=False,
)
console = Console()


class SyncMode(str, Enum):
    """Sync mode options."""

    ALL = "all"
    ENGLISH = "english"
    JAPANESE = "japanese"


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
    english_only: bool = typer.Option(
        False,
        "--english-only",
        "-e",
        help="Only sync English cards.",
    ),
    japanese_only: bool = typer.Option(
        False,
        "--japanese-only",
        "-j",
        help="Only sync Japanese card names.",
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
    """Sync card data from TCGdex to the database.

    By default, syncs both English cards and Japanese names.
    Use --english-only or --japanese-only to limit the sync scope.
    """
    setup_logging(verbose)

    # Validate options
    if english_only and japanese_only:
        console.print(
            "[red]Error:[/red] Cannot use --english-only and --japanese-only together."
        )
        raise typer.Exit(1)

    # Determine mode
    if english_only:
        mode = SyncMode.ENGLISH
    elif japanese_only:
        mode = SyncMode.JAPANESE
    else:
        mode = SyncMode.ALL

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] - No changes will be committed.\n")

    # Run the appropriate sync
    asyncio.run(_run_sync(mode, dry_run))


async def _run_sync(mode: SyncMode, dry_run: bool) -> None:
    """Run the sync operation.

    Args:
        mode: Which sync to run.
        dry_run: Whether to actually commit changes.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        if mode == SyncMode.ALL:
            task = progress.add_task("Syncing all cards...", total=None)
            english_result, japanese_count = await sync_all(dry_run=dry_run)
            progress.update(task, completed=True)

            console.print("\n[green]Sync complete![/green]")
            console.print("\n[bold]English Cards:[/bold]")
            console.print(f"  Sets processed: {english_result.sets_processed}")
            console.print(f"  Sets inserted:  {english_result.sets_inserted}")
            console.print(f"  Sets updated:   {english_result.sets_updated}")
            console.print(f"  Cards processed: {english_result.cards_processed}")
            if english_result.errors:
                console.print(f"  [red]Errors: {len(english_result.errors)}[/red]")
                for error in english_result.errors[:5]:
                    console.print(f"    - {error}")
                if len(english_result.errors) > 5:
                    console.print(f"    ... and {len(english_result.errors) - 5} more")

            console.print("\n[bold]Japanese Names:[/bold]")
            console.print(f"  Cards updated: {japanese_count}")

        elif mode == SyncMode.ENGLISH:
            task = progress.add_task("Syncing English cards...", total=None)
            result = await sync_english_cards(dry_run=dry_run)
            progress.update(task, completed=True)

            console.print("\n[green]English sync complete![/green]")
            console.print(f"  Sets processed: {result.sets_processed}")
            console.print(f"  Sets inserted:  {result.sets_inserted}")
            console.print(f"  Sets updated:   {result.sets_updated}")
            console.print(f"  Cards processed: {result.cards_processed}")
            if result.errors:
                console.print(f"  [red]Errors: {len(result.errors)}[/red]")

        elif mode == SyncMode.JAPANESE:
            task = progress.add_task("Syncing Japanese names...", total=None)
            updated_count = await sync_japanese_names(dry_run=dry_run)
            progress.update(task, completed=True)

            console.print("\n[green]Japanese name sync complete![/green]")
            console.print(f"  Cards updated: {updated_count}")


if __name__ == "__main__":
    app()
