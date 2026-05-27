"""CLI for viewing gac usage statistics."""

from datetime import datetime
from typing import Any

import click
from rich.panel import Panel
from rich.table import Table

from gac.config import load_config
from gac.stats import (
    compute_total_tokens,
    find_model_key,
    format_tokens,
    get_stats_summary,
    load_stats,
    model_activity,
    project_activity,
    reset_model_stats,
    reset_stats,
    stats_enabled,
)
from gac.stats.charts import build_bar_chart, format_latency, format_tps_value
from gac.utils import console


def _mark_current_model(model_name: str, current_model: str | None) -> str:
    """Append a * indicator if the model matches the currently configured model.

    Uses case-insensitive comparison via lower(), consistent with
    find_model_key() in gac.stats.store — keep both in sync.
    """
    if current_model and model_name.lower() == current_model.lower():
        return f"* {model_name}"
    return model_name


@click.group(invoke_without_command=True)
@click.pass_context
def stats(ctx: click.Context) -> None:
    """View your gac usage statistics."""
    if ctx.invoked_subcommand is None:
        ctx.forward(show)


@stats.command()
def show() -> None:
    """Show your gac usage statistics."""
    # Check if stats tracking is disabled
    if not stats_enabled():
        console.print("[dim]Stats tracking is currently disabled (GAC_DISABLE_STATS is set to a truthy value).[/dim]")
        console.print("[dim]Unset GAC_DISABLE_STATS or set it to 'false' to start tracking your gacs! 🚀[/dim]")
        return

    summary = get_stats_summary()
    total_gacs = summary.get("total_gacs", 0)
    total_commits = summary.get("total_commits", 0)
    total_tokens = summary.get("total_tokens", 0)

    if total_gacs == 0 and total_commits == 0 and total_tokens == 0:
        console.print("[yellow]No gacs yet! Time to start gaccing! 🚀[/yellow]")
        console.print("[dim]Run 'uvx gac' in a git repository to make your first commit.[/dim]")
        return

    # Main stats panel
    today_gacs = summary.get("today_gacs", 0)
    today_commits = summary.get("today_commits", 0)
    today_tokens = summary.get("today_tokens", 0)
    streak = summary["streak"]
    longest_streak = summary.get("longest_streak", 0)
    biggest_gac_tokens = summary.get("biggest_gac_tokens", 0)
    biggest_gac_date = summary.get("biggest_gac_date")
    biggest_gac_commits = summary.get("biggest_gac_commits", 0)
    biggest_gac_commits_date = summary.get("biggest_gac_commits_date")
    biggest_gac_files = summary.get("biggest_gac_files", 0)
    biggest_gac_files_date = summary.get("biggest_gac_files_date")
    peak_daily_gacs = summary.get("peak_daily_gacs", 0)
    peak_daily_commits = summary.get("peak_daily_commits", 0)
    peak_daily_tokens = summary.get("peak_daily_tokens", 0)
    week_gacs = summary.get("week_gacs", 0)
    week_commits = summary.get("week_commits", 0)
    week_tokens = summary.get("week_tokens", 0)
    peak_weekly_gacs = summary.get("peak_weekly_gacs", 0)
    peak_weekly_commits = summary.get("peak_weekly_commits", 0)
    peak_weekly_tokens = summary.get("peak_weekly_tokens", 0)

    # Compute previous peak (excluding today) to distinguish new records from ties
    today_str = datetime.now().strftime("%Y-%m-%d")
    prev_peak_gacs = max((v for d, v in summary.get("daily_gacs", {}).items() if d != today_str), default=0)
    prev_peak_commits = max((v for d, v in summary.get("daily_commits", {}).items() if d != today_str), default=0)
    prev_peak_tokens = max((v for d, v in summary.get("daily_total_tokens", {}).items() if d != today_str), default=0)
    # Previous weekly peak (excluding this week)
    iso_week = datetime.now().isocalendar()
    this_week_key = f"{iso_week[0]}-W{iso_week[1]:02d}"
    prev_peak_weekly_gacs = max((v for w, v in summary.get("weekly_gacs", {}).items() if w != this_week_key), default=0)
    prev_peak_weekly_commits = max(
        (v for w, v in summary.get("weekly_commits", {}).items() if w != this_week_key), default=0
    )
    prev_peak_weekly_tokens = max(
        (v for w, v in summary.get("weekly_total_tokens", {}).items() if w != this_week_key), default=0
    )
    # Previous longest streak: if current streak equals longest, the previous
    # record is longest_streak minus what today contributed (at most 1 day)
    prev_longest = longest_streak - 1 if streak == longest_streak and streak > 0 else longest_streak

    # Determine high scores for trophy display
    new_peak_gacs = today_gacs > 0 and today_gacs > prev_peak_gacs
    tied_peak_gacs = today_gacs > 0 and today_gacs == prev_peak_gacs
    new_peak_commits = today_commits > 0 and today_commits > prev_peak_commits
    tied_peak_commits = today_commits > 0 and today_commits == prev_peak_commits
    new_peak_tokens = today_tokens > 0 and today_tokens > prev_peak_tokens
    tied_peak_tokens = today_tokens > 0 and today_tokens == prev_peak_tokens
    new_peak_weekly_gacs = week_gacs > 0 and week_gacs > prev_peak_weekly_gacs
    tied_peak_weekly_gacs = week_gacs > 0 and week_gacs == prev_peak_weekly_gacs
    new_peak_weekly_commits = week_commits > 0 and week_commits > prev_peak_weekly_commits
    tied_peak_weekly_commits = week_commits > 0 and week_commits == prev_peak_weekly_commits
    new_peak_weekly_tokens = week_tokens > 0 and week_tokens > prev_peak_weekly_tokens
    tied_peak_weekly_tokens = week_tokens > 0 and week_tokens == prev_peak_weekly_tokens
    new_streak_record = streak > 0 and streak > prev_longest
    tied_streak_record = streak > 0 and streak == prev_longest

    # Detect if today set a new biggest-gac record
    new_biggest_gac = biggest_gac_tokens > 0 and biggest_gac_date == today_str
    new_biggest_gac_commits = biggest_gac_commits > 0 and biggest_gac_commits_date == today_str
    new_biggest_gac_files = biggest_gac_files > 0 and biggest_gac_files_date == today_str

    console.print()

    # Format the gac'd message (handles pluralization)
    if total_gacs == 1:
        gac_message = "You've gac'd [bold cyan]1[/bold cyan] time"
    else:
        gac_message = f"You've gac'd [bold cyan]{total_gacs}[/bold cyan] times"

    # Add commits info
    if total_commits == 1:
        commit_message = "creating [bold cyan]1[/bold cyan] commit"
    else:
        commit_message = f"creating [bold cyan]{total_commits}[/bold cyan] commits"

    console.print(
        Panel.fit(
            f"{gac_message}, {commit_message}!",
            title="🚀 GAC Stats",
            border_style="green",
        )
    )

    # Details table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="bold magenta")
    table.add_column("Value", style="bold")

    first_used = "[dim]/[/]".join(f"[bold cyan]{p}[/bold cyan]" for p in summary["first_used"].split("-"))
    last_used = "[dim]/[/]".join(f"[bold cyan]{p}[/bold cyan]" for p in summary["last_used"].split("-"))
    table.add_row("First gac", first_used)
    table.add_row("Last gac", last_used)
    streak_emoji = (
        " 🔥🏆" if new_streak_record and streak >= 5 else " 🏆" if new_streak_record else " 🔥" if streak >= 5 else ""
    )
    table.add_row(
        "Current streak",
        f"[bold cyan]{streak}[/bold cyan] [cyan]day{'s' if streak != 1 else ''}[/cyan]{streak_emoji}",
    )
    table.add_row(
        "Longest streak",
        f"[bold cyan]{longest_streak}[/bold cyan] [cyan]day{'s' if longest_streak != 1 else ''}[/cyan]",
    )

    console.print(table)

    # Biggest gacs section
    has_any_biggest = biggest_gac_tokens > 0 or biggest_gac_commits > 0 or biggest_gac_files > 0
    if has_any_biggest:
        console.print()
        console.print("[bold]Biggest Gacs:[/bold]")
        biggest_table = Table(show_header=True, box=None)
        biggest_table.add_column("Dimension", style="bold magenta")
        biggest_table.add_column("Record", style="bold cyan", justify="right")
        biggest_table.add_column("Date", style="bold")

        if biggest_gac_tokens > 0:
            date_str = (
                "[dim]/[/]".join(f"[bold cyan]{p}[/bold cyan]" for p in biggest_gac_date.split("-"))
                if biggest_gac_date
                else "—"
            )
            biggest_table.add_row("Tokens", format_tokens(biggest_gac_tokens), date_str)
        if biggest_gac_commits > 0:
            date_str = (
                "[dim]/[/]".join(f"[bold cyan]{p}[/bold cyan]" for p in biggest_gac_commits_date.split("-"))
                if biggest_gac_commits_date
                else "—"
            )
            biggest_table.add_row(
                "Commits",
                str(biggest_gac_commits),
                date_str,
            )
        if biggest_gac_files > 0:
            date_str = (
                "[dim]/[/]".join(f"[bold cyan]{p}[/bold cyan]" for p in biggest_gac_files_date.split("-"))
                if biggest_gac_files_date
                else "—"
            )
            biggest_table.add_row(
                "Files",
                str(biggest_gac_files),
                date_str,
            )

        console.print(biggest_table)

    # Activity summary table (today vs peak)
    console.print()
    console.print("[bold]Activity Summary:[/bold]")
    activity_table = Table(show_header=True, box=None)
    activity_table.add_column("Period", style="bold magenta")
    activity_table.add_column("Gacs", style="bold cyan", justify="right")
    activity_table.add_column("Commits", style="bold cyan", justify="right")
    activity_table.add_column("Tokens", style="bold cyan", justify="right")

    activity_table.add_row("Today", str(today_gacs), str(today_commits), format_tokens(today_tokens))
    activity_table.add_row("Peak Day", str(peak_daily_gacs), str(peak_daily_commits), format_tokens(peak_daily_tokens))
    activity_table.add_row("This Week", str(week_gacs), str(week_commits), format_tokens(week_tokens))
    activity_table.add_row(
        "Peak Week", str(peak_weekly_gacs), str(peak_weekly_commits), format_tokens(peak_weekly_tokens)
    )

    console.print(activity_table)

    # Top projects
    stats_data = load_stats()
    projects = stats_data.get("projects", {})
    if projects:
        console.print()
        console.print("[bold]Top Projects:[/bold]")
        projects_table = Table(show_header=True, box=None)
        projects_table.add_column("Project", style="bold magenta")
        projects_table.add_column("Gacs", style="bold cyan", justify="right")
        projects_table.add_column("Commits", style="bold cyan", justify="right")
        projects_table.add_column("Avg Files", style="bold cyan", justify="right")
        projects_table.add_column("Tokens", style="bold cyan", justify="right")

        sorted_projects = sorted(projects.items(), key=project_activity, reverse=True)

        # Show top 5 projects
        for project, data in sorted_projects[:5]:
            gacs = data.get("gacs", 0)
            commits = data.get("commits", 0)
            total_files = data.get("total_files", 0)
            if gacs > 0 and total_files > 0:
                avg_files = total_files / gacs
                avg_files_str = f"{avg_files:.1f}" if avg_files != int(avg_files) else str(int(avg_files))
            else:
                avg_files_str = "\u2014"
            tokens = compute_total_tokens(data)
            projects_table.add_row(project, str(gacs), str(commits), avg_files_str, format_tokens(tokens))

        console.print(projects_table)
        console.print()

    # Top models (from summary which includes computed avg_tps)
    top_models = summary.get("top_models", [])
    current_model = load_config().get("model") if top_models else None
    current_model_matched = False
    if top_models:
        console.print("[bold]Top Models:[/bold]")
        models_table = Table(show_header=True, box=None)
        models_table.add_column("Model", style="bold magenta", no_wrap=True)
        models_table.add_column("Gacs", style="bold cyan", justify="right")
        models_table.add_column("Commits", style="bold cyan", justify="right")
        models_table.add_column("Speed", style="bold cyan", justify="right")
        models_table.add_column("Latency", style="bold cyan", justify="right")
        models_table.add_column("Prompt", style="bold cyan", justify="right")
        models_table.add_column("Output", style="bold cyan", justify="right")
        models_table.add_column("Reasoning", style="bold cyan", justify="right")
        models_table.add_column("Total", style="bold cyan", justify="right")

        for model_name, data in top_models[:5]:
            gacs = data.get("gacs", 0)
            commits = data.get("commits", 0)
            prompt_t = int(data.get("prompt_tokens", 0))
            output_t = int(data.get("output_tokens", 0))
            reasoning_t = int(data.get("reasoning_tokens", 0))
            total_t = compute_total_tokens(data)
            avg_tps = data.get("avg_tps")
            speed_str = f"{format_tps_value(avg_tps)} tps" if avg_tps is not None else "\u2014"
            latency_str = format_latency(data["avg_latency_ms"]) if data.get("avg_latency_ms") is not None else "\u2014"
            reasoning_str = format_tokens(reasoning_t) if reasoning_t > 0 else "\u2014"
            marked = _mark_current_model(model_name, current_model)
            if marked != model_name:
                current_model_matched = True
            models_table.add_row(
                marked,
                str(gacs),
                str(commits),
                speed_str,
                latency_str,
                format_tokens(prompt_t),
                format_tokens(output_t),
                reasoning_str,
                format_tokens(total_t),
            )

        console.print(models_table)
        console.print()

    # Celebration and encouragement messages
    any_trophy = (
        new_peak_gacs
        or new_peak_commits
        or new_peak_tokens
        or new_peak_weekly_gacs
        or new_peak_weekly_commits
        or new_peak_weekly_tokens
        or new_streak_record
        or new_biggest_gac
        or new_biggest_gac_commits
        or new_biggest_gac_files
    )
    any_tie = (
        tied_peak_gacs
        or tied_peak_commits
        or tied_peak_tokens
        or tied_peak_weekly_gacs
        or tied_peak_weekly_commits
        or tied_peak_weekly_tokens
        or tied_streak_record
    )

    if today_gacs > 0 or any_trophy or any_tie:
        if new_biggest_gac:
            console.print("[bold yellow]🏆 New biggest gac record![/bold yellow]")
        if new_biggest_gac_commits:
            console.print("[bold yellow]🏆 New record for most commits in a gac![/bold yellow]")
        if new_biggest_gac_files:
            console.print("[bold yellow]🏆 New record for most files in a gac![/bold yellow]")
        if new_streak_record:
            console.print("[bold yellow]🏆 New longest streak record![/bold yellow]")
        elif tied_streak_record:  # pragma: no cover — mathematically unreachable with current prev_longest logic
            console.print("[yellow]🥈 Tied your longest streak record![/yellow]")
        if new_peak_gacs:
            console.print("[bold yellow]🏆 New daily high score for gacs![/bold yellow]")
        elif tied_peak_gacs:
            console.print("[yellow]🥈 Tied your daily high score for gacs![/yellow]")
        if new_peak_commits:
            console.print("[bold yellow]🏆 New daily high score for commits![/bold yellow]")
        elif tied_peak_commits:
            console.print("[yellow]🥈 Tied your daily high score for commits![/yellow]")
        if new_peak_tokens:
            console.print("[bold yellow]🏆 New daily high score for tokens![/bold yellow]")
        elif tied_peak_tokens:
            console.print("[yellow]🥈 Tied your daily high score for tokens![/yellow]")
        if new_peak_weekly_gacs:
            console.print("[bold yellow]🏆 New weekly high score for gacs![/bold yellow]")
        elif tied_peak_weekly_gacs:
            console.print("[yellow]🥈 Tied your weekly high score for gacs![/yellow]")
        if new_peak_weekly_commits:
            console.print("[bold yellow]🏆 New weekly high score for commits![/bold yellow]")
        elif tied_peak_weekly_commits:
            console.print("[yellow]🥈 Tied your weekly high score for commits![/yellow]")
        if new_peak_weekly_tokens:
            console.print("[bold yellow]🏆 New weekly high score for tokens![/bold yellow]")
        elif tied_peak_weekly_tokens:
            console.print("[yellow]🥈 Tied your weekly high score for tokens![/yellow]")
        if not (any_trophy or any_tie):
            if today_commits >= 5:
                console.print("[green]🔥 You're on fire today! Keep those commits flowing![/green]")
            elif streak >= 7:
                console.print("[green]🚀 Wow, a week-long streak! You're a gac machine![/green]")
            else:
                console.print("[green]✨ Nice work today! Every gac counts![/green]")
    elif streak > 0:
        console.print("[yellow]💪 Don't break that streak! Time for a gac![/yellow]")

    if current_model_matched:
        console.print()
        console.print("[dim]* currently selected model[/dim]")
    console.print()


@stats.command()
def models() -> None:
    """Show stats for all models (not just top 5)."""
    if not stats_enabled():
        console.print("[dim]Stats tracking is currently disabled (GAC_DISABLE_STATS is set to a truthy value).[/dim]")
        return

    stats_data = load_stats()
    models_data = stats_data.get("models", {})
    if not models_data:
        console.print("[yellow]No model usage yet! Time to start gaccing! 🚀[/yellow]")
        return

    sorted_models = sorted(models_data.items(), key=model_activity, reverse=True)

    from gac.stats.store import _enrich_models_with_speed

    enriched = _enrich_models_with_speed(sorted_models, history=stats_data.get("history", []))

    current_model = load_config().get("model")
    current_model_matched = False

    console.print()
    console.print("[bold]All Models:[/bold]")
    table = Table(show_header=True, box=None)
    table.add_column("Model", style="bold magenta", no_wrap=True)
    table.add_column("Gacs", style="bold cyan", justify="right")
    table.add_column("Commits", style="bold cyan", justify="right")
    table.add_column("Speed", style="bold cyan", justify="right")
    table.add_column("Latency", style="bold cyan", justify="right")
    table.add_column("Prompt", style="bold cyan", justify="right")
    table.add_column("Output", style="bold cyan", justify="right")
    table.add_column("Reasoning", style="bold cyan", justify="right")
    table.add_column("Total", style="bold cyan", justify="right")

    for model_name, data in enriched:
        gacs = data.get("gacs", 0)
        commits = data.get("commits", 0)
        prompt_t = int(data.get("prompt_tokens", 0))
        output_t = int(data.get("output_tokens", 0))
        reasoning_t = int(data.get("reasoning_tokens", 0))
        total_t = compute_total_tokens(data)
        avg_tps = data.get("avg_tps")
        speed_str = f"{format_tps_value(avg_tps)} tps" if avg_tps is not None else "\u2014"
        latency_str = format_latency(data["avg_latency_ms"]) if data.get("avg_latency_ms") is not None else "\u2014"
        reasoning_str = format_tokens(reasoning_t) if reasoning_t > 0 else "\u2014"
        marked = _mark_current_model(model_name, current_model)
        if marked != model_name:
            current_model_matched = True
        table.add_row(
            marked,
            str(gacs),
            str(commits),
            speed_str,
            latency_str,
            format_tokens(prompt_t),
            format_tokens(output_t),
            reasoning_str,
            format_tokens(total_t),
        )

    console.print(table)

    # TPS speed bar chart — prefer recent speed when available
    def _bar_tps(d: dict[str, Any]) -> float | None:
        v: float | None = d.get("recent_tps") if d.get("recent_tps") is not None else d.get("avg_tps")
        return v

    models_with_tps = [(name, d) for name, d in enriched if _bar_tps(d) is not None]
    if models_with_tps:
        models_with_tps.sort(key=lambda x: _bar_tps(x[1]) or 0, reverse=True)
        max_tps = max(_bar_tps(d) or 0 for _, d in models_with_tps)

        for _n, d in models_with_tps:
            d["_bar_tps"] = _bar_tps(d)

        console.print()
        console.print("[bold]Speed Comparison (30d):[/bold]")
        speed_table = build_bar_chart(
            models_with_tps,
            value_key="_bar_tps",
            max_value=float(max_tps),
            label_fmt=lambda v: f"{v:.0f} tps" if v >= 100 else f"{v:.1f} tps",
            higher_is_better=True,
            item_label_fmt=lambda name, _d, _r: _mark_current_model(name, current_model),
        )
        console.print(speed_table)

    # Latency bar chart — prefer recent latency when available
    def _bar_latency(d: dict[str, Any]) -> int | None:
        v: int | None = (
            d.get("recent_latency_ms") if d.get("recent_latency_ms") is not None else d.get("avg_latency_ms")
        )
        return v

    models_with_latency = [(name, d) for name, d in enriched if _bar_latency(d) is not None]
    if models_with_latency:
        models_with_latency.sort(key=lambda x: _bar_latency(x[1]) or 0)
        max_latency = max(_bar_latency(d) or 0 for _, d in models_with_latency)

        for _n, d in models_with_latency:
            d["_bar_latency"] = _bar_latency(d)

        console.print()
        console.print("[bold]Latency Comparison (30d):[/bold]")
        latency_table = build_bar_chart(
            models_with_latency,
            value_key="_bar_latency",
            max_value=float(max_latency),
            label_fmt=format_latency,
            higher_is_better=False,
            item_label_fmt=lambda name, _d, _r: _mark_current_model(name, current_model),
        )
        console.print(latency_table)

    # Per-commit latency bar chart — prefer recent when available
    def _bar_latency_per_commit(d: dict[str, Any]) -> int | None:
        v: int | None = (
            d.get("recent_latency_per_commit_ms")
            if d.get("recent_latency_per_commit_ms") is not None
            else d.get("avg_latency_per_commit_ms")
        )
        return v

    models_with_lpc = [(name, d) for name, d in enriched if _bar_latency_per_commit(d) is not None]
    if models_with_lpc:
        models_with_lpc.sort(key=lambda x: _bar_latency_per_commit(x[1]) or 0)
        max_lpc = max(_bar_latency_per_commit(d) or 0 for _, d in models_with_lpc)

        for _n, d in models_with_lpc:
            d["_bar_lpc"] = _bar_latency_per_commit(d)

        console.print()
        console.print("[bold]Per-Commit Latency (30d):[/bold]")
        lpc_table = build_bar_chart(
            models_with_lpc,
            value_key="_bar_lpc",
            max_value=float(max_lpc),
            label_fmt=format_latency,
            higher_is_better=False,
            item_label_fmt=lambda name, _d, _r: _mark_current_model(name, current_model),
        )
        console.print(lpc_table)

    if current_model_matched:
        console.print()
        console.print("[dim]* currently selected model[/dim]")
    console.print()


@stats.group(invoke_without_command=True)
@click.pass_context
def reset(ctx: click.Context) -> None:
    """Reset statistics (cannot be undone)."""
    if ctx.invoked_subcommand is None:
        # Default behavior: reset all stats (backward compatibility)
        console.print("[red]⚠️  This will delete all your gac statistics![/red]")
        console.print("[dim]Total commits, streaks, and history will be lost.[/dim]")
        console.print("[dim]Use 'uvx gac stats reset model <model-id>' to reset a specific model.[/dim]")
        console.print()

        confirm = click.confirm("Are you sure you want to reset all your stats?")
        if confirm:
            reset_stats()
            console.print("[green]Statistics reset. Starting fresh! 🚀[/green]")
        else:
            console.print("[dim]Reset cancelled. Your stats are safe![/dim]")


@reset.command()
@click.argument("model_id")
def model(model_id: str) -> None:
    """Reset statistics for a specific model (case-insensitive).

    MODEL_ID is the model identifier to reset (e.g. 'wafer:deepseek-v4-pro').
    The match is case-insensitive.
    """
    if not stats_enabled():
        console.print("[dim]Stats tracking is currently disabled (GAC_DISABLE_STATS is set to a truthy value).[/dim]")
        return

    stats_data = load_stats()
    models_data = stats_data.get("models", {})

    if not models_data:
        console.print("[yellow]No model statistics to reset![/yellow]")
        return

    # Find matching model (case-insensitive) using shared helper
    matched_key = find_model_key(models_data, model_id)

    if matched_key is None:
        console.print(f"[red]Model '[bold]{model_id}[/bold]' not found in statistics.[/red]")
        console.print("[dim]Available models:[/dim]")
        for key in sorted(models_data.keys()):
            console.print(f"  [dim]•[/dim] [cyan]{key}[/cyan]")
        return

    # Show what will be deleted
    model_data = models_data[matched_key]
    gacs = model_data.get("gacs", 0)
    total_tokens = compute_total_tokens(model_data)

    console.print(f"[yellow]This will reset statistics for model: [bold]{matched_key}[/bold][/yellow]")
    console.print(f"[dim]Gacs: {gacs}, Tokens: {format_tokens(total_tokens)}[/dim]")
    console.print()

    confirm = click.confirm("Are you sure you want to reset this model's stats?")
    if confirm:
        success = reset_model_stats(model_id)
        if success:
            console.print(f"[green]Statistics reset for model: {matched_key}[/green]")
        else:
            console.print(f"[red]Failed to reset model: {model_id}[/red]")
    else:
        console.print("[dim]Reset cancelled.[/dim]")
