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
"""

import sys

from rich.console import Console
from rich.panel import Panel

console = Console()

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
    console.print(f"  python main.py step1 --query \"yesterday's standup\"")
    console.print()


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

    if step_name == "step1" and "query" in kwargs:
        return module.run(meeting_query=kwargs["query"])
    return module.run()


def run_all():
    """Run all steps in sequence."""
    console.print(Panel.fit(
        "[bold]Running full pipeline[/bold]\n"
        "Meeting transcript → Plan → Repo → Issues → Agent → PRs",
        border_style="green",
    ))

    for step_name in STEPS:
        try:
            run_step(step_name)
        except SystemExit:
            console.print(f"\n[red]Pipeline stopped at {step_name}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error in {step_name}:[/red] {e}")
            sys.exit(1)

    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Pipeline complete![/bold green]")
    console.print("Check your GitHub repo for PRs to review.")
    console.print("=" * 60)


def cli():
    """CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        show_help()
        return

    step = args[0].lower()

    # Parse --query flag for step1
    kwargs = {}
    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 < len(args):
            kwargs["query"] = args[idx + 1]

    if step == "all":
        run_all()
    else:
        run_step(step, **kwargs)


if __name__ == "__main__":
    cli()
