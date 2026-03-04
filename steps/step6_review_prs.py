"""Step 6: Monitor PRs created by the Copilot coding agent.

Polls the repository for pull requests created by `copilot-swe-agent[bot]`
and displays their status for review.

Run:  python main.py step6
"""

import json

from github import Auth, Github
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import DATA_DIR, GITHUB_TOKEN

console = Console()


def review_prs() -> list[dict]:
    """List and display pull requests created by the Copilot coding agent.

    Returns:
        List of dicts with PR metadata.
    """
    console.print(Panel("[bold cyan]Step 6:[/] Reviewing PRs from Copilot coding agent", subtitle="GitHub API"))

    # Load repo info
    repo_path = DATA_DIR / "step3_repo.json"
    if not repo_path.exists():
        console.print("[red]✗[/red] No repo info found. Run step3 first.")
        raise SystemExit(1)
    repo_info = json.loads(repo_path.read_text())

    if not GITHUB_TOKEN:
        console.print("[red]✗[/red] GITHUB_TOKEN not set.")
        raise SystemExit(1)

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(repo_info["repo_name"])

    console.print(f"  Repo: [bold]{repo_info['repo_name']}[/bold]\n")

    # Get all open PRs
    pulls = repo.get_pulls(state="all", sort="created", direction="desc")

    copilot_prs = []
    table = Table(title="Pull Requests from Copilot Coding Agent")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("State", width=10)
    table.add_column("Author", width=20)
    table.add_column("URL")

    for pr in pulls:
        # Check if created by copilot-swe-agent
        author = pr.user.login if pr.user else "unknown"
        is_copilot = "copilot" in author.lower() or "bot" in author.lower()

        state_display = {
            "open": "[green]Open[/green]",
            "closed": "[red]Closed[/red]",
        }.get(pr.state, pr.state)

        if pr.merged:
            state_display = "[purple]Merged[/purple]"

        pr_info = {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "merged": pr.merged if hasattr(pr, "merged") else False,
            "author": author,
            "url": pr.html_url,
            "created_at": str(pr.created_at),
            "is_copilot": is_copilot,
        }
        copilot_prs.append(pr_info)

        table.add_row(
            str(pr.number),
            pr.title,
            state_display,
            f"[cyan]{author}[/cyan]" if is_copilot else author,
            pr.html_url,
        )

    if copilot_prs:
        console.print(table)

        agent_prs = [pr for pr in copilot_prs if pr["is_copilot"]]
        console.print(f"\n  Total PRs:          [bold]{len(copilot_prs)}[/bold]")
        console.print(f"  From Copilot agent: [bold]{len(agent_prs)}[/bold]")

        open_prs = [pr for pr in agent_prs if pr["state"] == "open"]
        if open_prs:
            console.print(f"\n[yellow]→[/yellow] [bold]{len(open_prs)}[/bold] PR(s) awaiting your review:")
            for pr in open_prs:
                console.print(f"  [link={pr['url']}]#{pr['number']} {pr['title']}[/link]")
    else:
        console.print("[yellow]⚠[/yellow] No pull requests found yet.")
        console.print("[dim]The coding agent may still be working. Try again in a few minutes.[/dim]")

    # Save PR info
    output_path = DATA_DIR / "step6_prs.json"
    output_path.write_text(json.dumps(copilot_prs, indent=2))
    console.print(f"\n[green]✓[/green] PR info saved to [bold]{output_path}[/bold]")

    g.close()
    return copilot_prs


def run():
    """Entry point for Step 6."""
    return review_prs()
