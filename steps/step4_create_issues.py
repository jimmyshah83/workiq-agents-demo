"""Step 4: Create GitHub issues from the implementation plan.

Uses PyGithub to create issues in the repo created in Step 3,
based on the plan from Step 2.

Run:  python main.py step4
"""

import json

from github import Auth, Github
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import DATA_DIR, GITHUB_TOKEN

console = Console()


def create_issues() -> list[dict]:
    """Create GitHub issues from the plan.

    Reads the plan from data/step2_plan.json and repo info from
    data/step3_repo.json, then creates one issue per planned task.

    Returns:
        List of dicts with issue metadata (number, title, url).
    """
    console.print(Panel("[bold cyan]Step 4:[/] Creating GitHub issues", subtitle="GitHub API"))

    # Load plan
    plan_path = DATA_DIR / "step2_plan.json"
    if not plan_path.exists():
        console.print("[red]✗[/red] No plan found. Run step2 first.")
        raise SystemExit(1)
    plan = json.loads(plan_path.read_text())

    # Load repo info
    repo_path = DATA_DIR / "step3_repo.json"
    if not repo_path.exists():
        console.print("[red]✗[/red] No repo info found. Run step3 first.")
        raise SystemExit(1)
    repo_info = json.loads(repo_path.read_text())

    if not GITHUB_TOKEN:
        console.print("[red]✗[/red] GITHUB_TOKEN not set.")
        raise SystemExit(1)

    issues_list = plan.get("issues", [])
    if not issues_list:
        console.print("[yellow]⚠[/yellow] No issues in the plan.")
        return []

    console.print(f"  Repo:   [bold]{repo_info['repo_name']}[/bold]")
    console.print(f"  Issues: [bold]{len(issues_list)}[/bold] to create\n")

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(repo_info["repo_name"])

    created_issues = []
    table = Table(title="Created Issues")
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Labels")
    table.add_column("URL")

    for i, issue_data in enumerate(issues_list, 1):
        title = issue_data.get("title", f"Task {i}")
        body = issue_data.get("description", "")
        labels = issue_data.get("labels", [])
        priority = issue_data.get("priority", "medium")

        # Add priority and dependencies info to body
        body_parts = [body]
        if priority:
            body_parts.append(f"\n**Priority:** {priority}")
        deps = issue_data.get("dependencies", [])
        if deps:
            body_parts.append(f"**Dependencies:** {', '.join(str(d) for d in deps)}")

        full_body = "\n".join(body_parts)

        try:
            # Create labels that don't exist yet
            existing_labels = [l.name for l in repo.get_labels()]
            for label in labels:
                if label not in existing_labels:
                    try:
                        repo.create_label(name=label, color="0075ca")
                        existing_labels.append(label)
                    except Exception:
                        pass  # Label might already exist (race condition)

            issue = repo.create_issue(
                title=title,
                body=full_body,
                labels=labels,
            )

            issue_info = {
                "number": issue.number,
                "title": title,
                "url": issue.html_url,
                "labels": labels,
                "priority": priority,
            }
            created_issues.append(issue_info)

            table.add_row(
                str(issue.number),
                title,
                ", ".join(labels),
                issue.html_url,
            )

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create issue '{title}': {e}")

    console.print(table)
    console.print(f"\n[green]✓[/green] Created [bold]{len(created_issues)}[/bold] issues")

    # Save issues info
    output_path = DATA_DIR / "step4_issues.json"
    output_path.write_text(json.dumps(created_issues, indent=2))
    console.print(f"[green]✓[/green] Issues info saved to [bold]{output_path}[/bold]")

    g.close()
    return created_issues


def run():
    """Entry point for Step 4."""
    return create_issues()
