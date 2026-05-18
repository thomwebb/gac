"""Stats subcommands for projects and recent gac history.

These commands are registered on the ``stats`` Click group defined in
``gac.stats_cli``.  Importing this module has the side-effect of adding
the commands to the group, so the import must happen before Click
resolves the group's commands.
"""

import click
from rich.panel import Panel
from rich.table import Table

from gac.stats import (
    compute_total_tokens,
    format_tokens,
    load_stats,
    project_activity,
    stats_enabled,
)
from gac.stats.charts import build_bar_chart, format_latency, format_relative_time, format_tps, project_rank_label
from gac.stats_cli import stats
from gac.utils import console

# ─── recent ──────────────────────────────────────────────────────────────────


@stats.command()
@click.option("-n", "--number", default=10, help="Number of recent gacs to show.")
def recent(number: int) -> None:
    """Show your most recent gacs with per-gac metadata."""
    if not stats_enabled():
        console.print("[dim]Stats tracking is currently disabled (GAC_DISABLE_STATS is set to a truthy value).[/dim]")
        return

    stats_data = load_stats()
    history = stats_data.get("history", [])

    if not history:
        console.print("[yellow]No gac history yet! Time to start gaccing! 🚀[/yellow]")
        console.print("[dim]History tracking starts with v4 stats schema.[/dim]")
        return

    # Show most recent first
    recent_gacs = list(reversed(history[-number:]))

    console.print()
    console.print(
        Panel.fit(
            f"Last [bold cyan]{len(recent_gacs)}[/bold cyan] gac{'s' if len(recent_gacs) != 1 else ''}",
            title="🕐 Recent Gacs",
            border_style="blue",
        )
    )

    table = Table(show_header=True, box=None)
    table.add_column("When", style="bold blue")
    table.add_column("Project", style="bold magenta", min_width=10)
    table.add_column("Model", style="bold cyan", no_wrap=True)
    table.add_column("Commits", style="bold cyan", justify="right")
    table.add_column("Files", style="bold cyan", justify="right")
    table.add_column("Speed", style="bold cyan", justify="right")
    table.add_column("Latency", style="bold cyan", justify="right")
    table.add_column("Prompt", style="bold cyan", justify="right")
    table.add_column("Output", style="bold cyan", justify="right")
    table.add_column("Reasoning", style="bold cyan", justify="right")
    table.add_column("Total", style="bold cyan", justify="right")

    for gac in recent_gacs:
        ts = gac.get("ts", "")
        when = format_relative_time(ts)
        project = gac.get("project") or "\u2014"
        model_name = gac.get("model") or "\u2014"
        commits = gac.get("commits", 0)
        files = gac.get("files", 0)
        files_str = str(files) if files > 0 else "\u2014"
        prompt_t = gac.get("prompt_tokens", 0)
        output_t = gac.get("output_tokens", 0)
        reasoning_t = gac.get("reasoning_tokens", 0)
        total_t = prompt_t + output_t + reasoning_t
        duration_ms = gac.get("duration_ms", 0)
        tps_str = format_tps(output_t, reasoning_t, duration_ms)
        latency_str = format_latency(duration_ms) if duration_ms > 0 else "\u2014"
        reasoning_str = format_tokens(reasoning_t) if reasoning_t > 0 else "\u2014"

        table.add_row(
            when,
            project,
            model_name,
            str(commits),
            files_str,
            tps_str,
            latency_str,
            format_tokens(prompt_t),
            format_tokens(output_t),
            reasoning_str,
            format_tokens(total_t),
        )

    console.print(table)
    console.print()


# ─── projects ─────────────────────────────────────────────────────────────────


@stats.command()
def projects() -> None:
    """Show stats for all projects (not just top 5)."""
    if not stats_enabled():
        console.print("[dim]Stats tracking is currently disabled (GAC_DISABLE_STATS is set to a truthy value).[/dim]")
        return

    stats_data = load_stats()
    projects_data = stats_data.get("projects", {})
    if not projects_data:
        console.print("[yellow]No project usage yet! Time to start gaccing! 🚀[/yellow]")
        return

    sorted_projects = sorted(projects_data.items(), key=project_activity, reverse=True)

    # Compute overall totals for percentage calculations
    total_gacs = stats_data.get("total_gacs", 0)

    num_projects = len(sorted_projects)
    project_label = "project" if num_projects == 1 else "projects"

    console.print()
    console.print(
        Panel.fit(
            f"You've gac'd across [bold cyan]{num_projects}[/bold cyan] {project_label}!",
            title="📁 Projects",
            border_style="magenta",
        )
    )

    # Detail table with rank medals, efficiency, and percentage
    table = Table(show_header=True, box=None)
    table.add_column("Project", style="bold magenta")
    table.add_column("Gacs", style="bold cyan", justify="right")
    table.add_column("Commits", style="bold cyan", justify="right")
    table.add_column("C/G", style="bold cyan", justify="right")
    table.add_column("Avg Files", style="bold cyan", justify="right")
    table.add_column("Prompt", style="bold cyan", justify="right")
    table.add_column("Output", style="bold cyan", justify="right")
    table.add_column("Reasoning", style="bold cyan", justify="right")
    table.add_column("Total", style="bold cyan", justify="right")
    table.add_column("Share", style="bold cyan", justify="right")

    for rank, (project_name, data) in enumerate(sorted_projects, 1):
        gacs = data.get("gacs", 0)
        commits = data.get("commits", 0)
        prompt_t = int(data.get("prompt_tokens", 0))
        output_t = int(data.get("output_tokens", 0))
        reasoning_t = int(data.get("reasoning_tokens", 0))
        total_t = compute_total_tokens(data)
        reasoning_str = format_tokens(reasoning_t) if reasoning_t > 0 else "\u2014"

        # Commits per gac efficiency
        if gacs > 0:
            cg_ratio = commits / gacs
            cg_str = f"{cg_ratio:.1f}" if cg_ratio != int(cg_ratio) else str(int(cg_ratio))
        else:
            cg_str = "\u2014"

        # Avg files per gac
        total_files = data.get("total_files", 0)
        if gacs > 0 and total_files > 0:
            avg_files = total_files / gacs
            avg_files_str = f"{avg_files:.1f}" if avg_files != int(avg_files) else str(int(avg_files))
        else:
            avg_files_str = "\u2014"

        # Percentage of total gacs
        gac_pct = (gacs / total_gacs * 100) if total_gacs > 0 else 0
        share_str = f"{gac_pct:.0f}%"

        label = project_rank_label(rank, project_name)
        table.add_row(
            label,
            str(gacs),
            str(commits),
            cg_str,
            avg_files_str,
            format_tokens(prompt_t),
            format_tokens(output_t),
            reasoning_str,
            format_tokens(total_t),
            share_str,
        )

    console.print(table)

    # Gacs bar chart
    max_gacs = max(d.get("gacs", 0) for _, d in sorted_projects) if sorted_projects else 0
    if max_gacs > 0:
        console.print()
        console.print("[bold]Activity:[/bold]")
        gacs_chart = build_bar_chart(
            sorted_projects,
            value_key="gacs",
            max_value=max_gacs,
            label_fmt=lambda v: f"{v} gac{'s' if v != 1 else ''}",
            higher_is_better=True,
            item_label_fmt=lambda name, _d, rank: project_rank_label(rank, name),
        )
        console.print(gacs_chart)

    # Tokens bar chart
    # Pre-compute total tokens per project for the chart
    projects_with_totals = []
    for name, data in sorted_projects:
        enriched = {**data, "total_tokens": compute_total_tokens(data)}
        projects_with_totals.append((name, enriched))

    max_tokens = max(d["total_tokens"] for _, d in projects_with_totals) if projects_with_totals else 0
    if max_tokens > 0:
        console.print()
        console.print("[bold]Token Usage:[/bold]")
        tokens_chart = build_bar_chart(
            projects_with_totals,
            value_key="total_tokens",
            max_value=max_tokens,
            label_fmt=format_tokens,
            higher_is_better=True,
            item_label_fmt=lambda name, _d, rank: project_rank_label(rank, name),
        )
        console.print(tokens_chart)

    # Fun facts
    if len(sorted_projects) >= 2:
        top_name, top_data = sorted_projects[0]
        top_gacs = top_data.get("gacs", 0)
        top_share = (top_gacs / total_gacs * 100) if total_gacs > 0 else 0
        console.print()
        if top_share >= 50:
            console.print(
                f"[bold yellow]🏆 {top_name}[/bold yellow] accounts for [bold cyan]{top_share:.0f}%[/bold cyan] of all your gacs!"
            )
        elif top_share >= 30:
            console.print(
                f"[green]⭐ {top_name}[/green] leads the pack with [bold cyan]{top_share:.0f}%[/bold cyan] of all gacs."
            )
        else:
            console.print("[cyan]📊 Your attention is spread across projects — no single project dominates![/cyan]")

        # Most efficient project (highest commits/gac with >1 gac)
        candidates = [(n, d) for n, d in sorted_projects if d.get("gacs", 0) > 1]
        if candidates:
            best_name, best_data = max(candidates, key=lambda x: x[1].get("commits", 0) / x[1].get("gacs", 1))
            best_cg = best_data["commits"] / best_data["gacs"]
            if best_cg > 1.5:  # Only show if meaningfully above 1:1
                console.print(
                    f"[green]🔥 {best_name}[/green] is your most productive project: [bold cyan]{best_cg:.1f}[/bold cyan] commits per gac!"
                )

    console.print()
