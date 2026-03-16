"""Step 3: Create a GitHub repository for the project.

Uses PyGithub to create a new repo based on the plan from Step 2.

Run:  python main.py step3
"""

import json

from github import Auth, Github
from rich.console import Console
from rich.panel import Panel

from config import DATA_DIR, GITHUB_OWNER, GITHUB_TOKEN

console = Console()


def create_repo(repo_name: str | None = None, description: str | None = None) -> dict:
    """Create a new GitHub repository.

    Args:
        repo_name: Repository name. If None, reads from the plan.
        description: Repository description. If None, reads from the plan.

    Returns:
        dict with repo metadata (name, url, clone_url).
    """
    console.print(Panel("[bold cyan]Step 3:[/] Creating GitHub repository", subtitle="GitHub API"))

    # Load plan if needed
    plan_path = DATA_DIR / "step2_plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text())
        if repo_name is None:
            repo_name = plan.get("project_name", "new-project")
        if description is None:
            description = plan.get("project_description", "Project created from meeting transcript")
    else:
        if repo_name is None:
            console.print("[red]✗[/red] No plan found and no repo name provided. Run step2 first.")
            raise SystemExit(1)

    if not GITHUB_TOKEN:
        console.print("[red]✗[/red] GITHUB_TOKEN not set. Add it to your .env file.")
        raise SystemExit(1)

    console.print(f"  Repo name:    [bold]{repo_name}[/bold]")
    console.print(f"  Description:  [italic]{description}[/italic]\n")

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)

    try:
        user = g.get_user()
        repo = user.create_repo(
            name=repo_name,
            description=description or "",
            auto_init=True,
            private=False,
        )

        result = {
            "repo_name": repo.full_name,
            "repo_url": repo.html_url,
            "clone_url": repo.clone_url,
            "default_branch": repo.default_branch,
        }

        console.print(f"[green]✓[/green] Repository created: [bold link={repo.html_url}]{repo.full_name}[/bold link]")
        console.print(f"  URL:   {repo.html_url}")
        console.print(f"  Clone: {repo.clone_url}")

        # Save repo info
        output_path = DATA_DIR / "step3_repo.json"
        output_path.write_text(json.dumps(result, indent=2))
        console.print(f"\n[green]✓[/green] Repo info saved to [bold]{output_path}[/bold]")

        g.close()
        return result

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create repo: {e}")
        g.close()
        raise


def run():
    """Entry point for Step 3."""
    return create_repo()
