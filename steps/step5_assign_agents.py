"""Step 5: Assign the GitHub Copilot coding agent to each issue.

Uses the GitHub REST API to assign `copilot-swe-agent[bot]` to issues
created in Step 4, triggering the agent to start working on each one.

Run:  python main.py step5
"""

import json
import time

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import DATA_DIR, GITHUB_TOKEN

console = Console()

GITHUB_API = "https://api.github.com"


def assign_agents() -> list[dict]:
    """Assign the Copilot coding agent to each issue.

    Uses the REST API endpoint:
        POST /repos/{owner}/{repo}/issues/{issue_number}/assignees

    With the special assignee `copilot-swe-agent[bot]` and an optional
    `agent_assignment` payload to customize the task.

    Returns:
        List of dicts with assignment results.
    """
    console.print(Panel("[bold cyan]Step 5:[/] Assigning Copilot coding agent to issues", subtitle="GitHub API"))

    # Load repo info
    repo_path = DATA_DIR / "step3_repo.json"
    if not repo_path.exists():
        console.print("[red]✗[/red] No repo info found. Run step3 first.")
        raise SystemExit(1)
    repo_info = json.loads(repo_path.read_text())

    # Load issues info
    issues_path = DATA_DIR / "step4_issues.json"
    if not issues_path.exists():
        console.print("[red]✗[/red] No issues info found. Run step4 first.")
        raise SystemExit(1)
    issues = json.loads(issues_path.read_text())

    if not GITHUB_TOKEN:
        console.print("[red]✗[/red] GITHUB_TOKEN not set.")
        raise SystemExit(1)

    repo_name = repo_info["repo_name"]
    default_branch = repo_info.get("default_branch", "main")

    console.print(f"  Repo:    [bold]{repo_name}[/bold]")
    console.print(f"  Branch:  [bold]{default_branch}[/bold]")
    console.print(f"  Issues:  [bold]{len(issues)}[/bold] to assign\n")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    results = []
    table = Table(title="Agent Assignments")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Status")

    for issue in issues:
        issue_number = issue["number"]
        title = issue["title"]

        payload = {
            "assignees": ["copilot-swe-agent[bot]"],
            "agent_assignment": {
                "target_repo": repo_name,
                "base_branch": default_branch,
                "custom_instructions": "",
                "custom_agent": "",
                "model": "",
            },
        }

        url = f"{GITHUB_API}/repos/{repo_name}/issues/{issue_number}/assignees"
        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code in (200, 201):
            result = {
                "issue_number": issue_number,
                "title": title,
                "status": "assigned",
                "url": issue["url"],
            }
            table.add_row(str(issue_number), title, "[green]✓ Assigned[/green]")
        else:
            error_msg = resp.json().get("message", resp.text)
            result = {
                "issue_number": issue_number,
                "title": title,
                "status": "failed",
                "error": error_msg,
            }
            table.add_row(str(issue_number), title, f"[red]✗ {error_msg}[/red]")

        results.append(result)

        # Small delay between assignments to avoid rate limiting
        time.sleep(1)

    console.print(table)

    assigned_count = sum(1 for r in results if r["status"] == "assigned")
    console.print(f"\n[green]✓[/green] Assigned [bold]{assigned_count}/{len(issues)}[/bold] issues to Copilot coding agent")
    console.print("[dim]The coding agent will now start working on each issue and create PRs.[/dim]")

    # Save assignment results
    output_path = DATA_DIR / "step5_assignments.json"
    output_path.write_text(json.dumps(results, indent=2))
    console.print(f"[green]✓[/green] Assignment results saved to [bold]{output_path}[/bold]")

    return results


def run():
    """Entry point for Step 5."""
    return assign_agents()
