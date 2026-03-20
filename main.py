#!/usr/bin/env python3
"""Work IQ → GitHub Copilot Agent Pipeline

A step-by-step CLI that:
  1. Reads meeting transcripts from Microsoft 365 via Work IQ
  2. Plans implementation tasks using the GitHub Copilot SDK
  3. Creates a GitHub repository
  4. Creates GitHub issues from the plan
  5. Assigns the Copilot coding agent to execute each issue
  6. Monitors PRs created by the agent for your review

Usage:
    python main.py step1                # Read meeting transcript
    python main.py step2                # Plan tasks from transcript
    python main.py step3                # Create GitHub repo
    python main.py step4                # Create issues
    python main.py step5                # Assign coding agent
    python main.py step6                # Review PRs
    python main.py all                  # Run all steps
    python main.py step1 --query "yesterday's standup"
    python main.py all --name "Sprint Planning"  # Full pipeline for a meeting by name
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

DATA_DIR = Path(__file__).parent / "data"

STEPS = {
    "step1": ("Read meeting transcript (Work IQ)", "steps.step1_read_transcript"),
    "step2": ("Plan implementation tasks (Copilot SDK)", "steps.step2_plan_tasks"),
    "step3": ("Create GitHub repository", "steps.step3_create_repo"),
    "step4": ("Create GitHub issues", "steps.step4_create_issues"),
    "step5": ("Assign Copilot coding agent", "steps.step5_assign_agents"),
    "step6": ("Review pull requests", "steps.step6_review_prs"),
}


def show_help():
    console.print(Panel.fit(
        "[bold]Work IQ → GitHub Copilot Agent Pipeline[/bold]\n\n"
        "Transform meeting transcripts into implemented code, automatically.",
        border_style="cyan",
    ))
    console.print("\n[bold]Available steps:[/bold]\n")
    for key, (desc, _) in STEPS.items():
        console.print(f"  [cyan]{key}[/cyan]  {desc}")
    console.print(f"  [cyan]all [/cyan]  Run all steps sequentially")
    console.print(f"\n[bold]Usage:[/bold]")
    console.print(f"  python main.py <step>")
    console.print(f"  python main.py step1 --query \"yesterday's standup\"\n")


def run_step(step_name: str, **kwargs):
    """Import and run a single step."""
    if step_name not in STEPS:
        console.print(f"[red]Unknown step:[/red] {step_name}")
        show_help()
        sys.exit(1)

    desc, module_path = STEPS[step_name]
    console.print(f"\n{'─' * 60}")
    console.print(f"  [bold cyan]Running:[/bold cyan] {desc}")
    console.print(f"{'─' * 60}\n")

    import importlib
    module = importlib.import_module(module_path)

    if step_name == "step1":
        return module.run(
            meeting_query=kwargs.get("query"),
            meeting_name=kwargs.get("name"),
        )
    return module.run()


def _print_linkedin_summary():
    """Print a rich, LinkedIn-ready summary of the full pipeline run."""
    # Gather data from each step's output
    transcript_data = {}
    plan_data = {}
    repo_data = {}
    issues_data = []
    assignments_data = []
    prs_data = []

    for name, path in [
        ("transcript", DATA_DIR / "step1_transcript.json"),
        ("plan", DATA_DIR / "step2_plan.json"),
        ("repo", DATA_DIR / "step3_repo.json"),
        ("issues", DATA_DIR / "step4_issues.json"),
        ("assignments", DATA_DIR / "step5_assignments.json"),
        ("prs", DATA_DIR / "step6_prs.json"),
    ]:
        if path.exists():
            data = json.loads(path.read_text())
            if name == "transcript":
                transcript_data = data
            elif name == "plan":
                plan_data = data
            elif name == "repo":
                repo_data = data
            elif name == "issues":
                issues_data = data
            elif name == "assignments":
                assignments_data = data
            elif name == "prs":
                prs_data = data

    # ── Pipeline Results Table ──
    results_table = Table(
        title="\n🚀 Pipeline Results",
        show_header=True,
        header_style="bold cyan",
        border_style="bright_blue",
        title_style="bold white",
        padding=(0, 2),
    )
    results_table.add_column("Step", style="bold", width=8)
    results_table.add_column("Action", width=38)
    results_table.add_column("Result", style="green")

    # Step 1
    meeting = transcript_data.get("meeting_query", "N/A")
    meeting_short = meeting[:60] + "…" if len(meeting) > 60 else meeting
    results_table.add_row("Step 1", "📋 Read Meeting Transcript", f"✅ {meeting_short}")

    # Step 2
    project = plan_data.get("project_name", "N/A")
    num_issues = len(plan_data.get("issues", []))
    tech_stack = ", ".join(plan_data.get("tech_stack", []))
    results_table.add_row("Step 2", "🧠 AI-Planned Tasks", f"✅ {num_issues} issues • {tech_stack}")

    # Step 3
    repo_url = repo_data.get("repo_url", "N/A")
    repo_name = repo_data.get("repo_name", "N/A")
    results_table.add_row("Step 3", "📦 Created GitHub Repo", f"✅ {repo_name}")

    # Step 4
    results_table.add_row("Step 4", "🎫 Created GitHub Issues", f"✅ {len(issues_data)} issues")

    # Step 5
    assigned = sum(1 for a in assignments_data if a.get("status") == "assigned")
    results_table.add_row("Step 5", "🤖 Assigned Copilot Agent", f"✅ {assigned} agents dispatched")

    # Step 6
    agent_prs = [p for p in prs_data if p.get("is_copilot")]
    open_prs = [p for p in agent_prs if p.get("state") == "open"]
    results_table.add_row("Step 6", "🔍 Reviewed Pull Requests", f"✅ {len(agent_prs)} PRs ({len(open_prs)} open)")

    console.print(results_table)

    # ── LinkedIn Summary ──
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    summary_lines = [
        "",
        "🎯 [bold white]From Meeting to Merged Code — Fully Automated[/bold white]",
        "",
        f"Today I turned a [bold]Teams meeting[/bold] into a [bold]working codebase[/bold]",
        "using a 6-step AI-powered pipeline:",
        "",
        f"  📋  [cyan]Work IQ[/cyan] extracted the meeting transcript from Microsoft 365",
        f"  🧠  [cyan]GitHub Copilot SDK[/cyan] analyzed it and planned {num_issues} implementation tasks",
        f"  📦  Created repo [bold]{repo_name}[/bold]",
        f"  🎫  Filed {len(issues_data)} well-scoped GitHub issues automatically",
        f"  🤖  Assigned the [bold]Copilot coding agent[/bold] to implement each one",
        f"  🔍  {len(agent_prs)} pull requests created and ready for review",
        "",
        f"  🔗  [link={repo_url}]{repo_url}[/link]",
        "",
        "  [dim]Tech stack:[/dim] [bold]{stack}[/bold]".format(stack=tech_stack or "TBD"),
        f"  [dim]Completed:[/dim]  [bold]{timestamp}[/bold]",
        "",
        "  [dim italic]#AI #GitHubCopilot #WorkIQ #Microsoft365 #DevProductivity[/dim italic]",
    ]

    console.print(Panel(
        "\n".join(summary_lines),
        title="✨ LinkedIn Summary ✨",
        border_style="bright_magenta",
        padding=(1, 3),
    ))


def run_all(**kwargs):
    """Run all steps in sequence."""
    console.print(Panel.fit(
        "[bold]Running full pipeline[/bold]\n"
        "Meeting transcript → Plan → Repo → Issues → Agent → PRs",
        border_style="green",
    ))

    for step_name in STEPS:
        try:
            if step_name == "step1":
                run_step(step_name, **kwargs)
            else:
                run_step(step_name)
        except SystemExit:
            console.print(f"\n[red]Pipeline stopped at {step_name}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error in {step_name}:[/red] {e}")
            sys.exit(1)

    _print_linkedin_summary()


def cli():
    """CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        show_help()
        return

    step = args[0].lower()

    # Parse flags for step1
    kwargs = {}
    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 < len(args):
            kwargs["query"] = args[idx + 1]
    if "--name" in args:
        idx = args.index("--name")
        if idx + 1 < len(args):
            kwargs["name"] = args[idx + 1]

    if step == "all":
        run_all(**kwargs)
    else:
        run_step(step, **kwargs)


if __name__ == "__main__":
    cli()
