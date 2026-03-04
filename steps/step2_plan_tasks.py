"""Step 2: Analyze the meeting transcript and plan implementation tasks.

Uses the GitHub Copilot SDK to break down the meeting transcript
into a structured plan of GitHub issues with descriptions.

Run:  python main.py step2
"""

import asyncio
import json
from pathlib import Path

from copilot import CopilotClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import COPILOT_MODEL, DATA_DIR

console = Console()

PLAN_SCHEMA = """\
Return your plan as a JSON object with this exact structure:
{
  "project_name": "short-kebab-case-name",
  "project_description": "One-line description of the project",
  "tech_stack": ["python", "fastapi", ...],
  "issues": [
    {
      "title": "Short issue title",
      "description": "Detailed description with acceptance criteria",
      "labels": ["enhancement", "backend"],
      "priority": "high|medium|low",
      "dependencies": []
    }
  ]
}

IMPORTANT: Return ONLY the JSON object, no markdown fencing or extra text.\
"""


async def plan_tasks(transcript: str | None = None) -> dict:
    """Analyze a meeting transcript and produce a structured plan.

    Args:
        transcript: The meeting transcript text. If None, reads from
            data/step1_transcript.json (output of Step 1).

    Returns:
        dict with project metadata and list of issues.
    """
    if transcript is None:
        transcript_path = DATA_DIR / "step1_transcript.json"
        if not transcript_path.exists():
            console.print("[red]✗[/red] No transcript found. Run step1 first.")
            raise SystemExit(1)
        data = json.loads(transcript_path.read_text())
        transcript = data["transcript"]

    console.print(Panel("[bold cyan]Step 2:[/] Planning implementation tasks", subtitle="Copilot SDK"))
    console.print(f"  Transcript length: [bold]{len(transcript)}[/bold] characters\n")

    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": COPILOT_MODEL,
    })

    collected_response = []
    done = asyncio.Event()

    def on_event(event):
        event_type = event.type.value if hasattr(event.type, "value") else str(event.type)
        if event_type == "assistant.message":
            collected_response.append(event.data.content or "")
        elif event_type == "session.idle":
            done.set()

    session.on(on_event)

    prompt = f"""You are a senior software architect. Analyze the following meeting transcript
and create a detailed implementation plan as GitHub issues.

Break the work into well-scoped, independent issues that a coding agent can execute.
Each issue should be self-contained with clear acceptance criteria.
Order them by dependency (issues with no dependencies first).

MEETING TRANSCRIPT:
---
{transcript}
---

{PLAN_SCHEMA}"""

    console.print("[dim]Analyzing transcript and creating plan...[/dim]\n")
    await session.send({"prompt": prompt})
    await done.wait()

    full_response = "".join(collected_response)

    # Parse the JSON plan from the response
    try:
        # Try to extract JSON from the response (handle markdown fencing)
        json_str = full_response.strip()
        if json_str.startswith("```"):
            # Remove markdown code fences
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])
        plan = json.loads(json_str)
    except json.JSONDecodeError:
        console.print("[yellow]Warning:[/yellow] Could not parse JSON directly, saving raw response.")
        plan = {"raw_response": full_response, "issues": []}

    # Display the plan
    if "issues" in plan and plan["issues"]:
        table = Table(title="Implementation Plan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="bold")
        table.add_column("Priority", width=8)
        table.add_column("Labels")

        for i, issue in enumerate(plan["issues"], 1):
            table.add_row(
                str(i),
                issue.get("title", "Untitled"),
                issue.get("priority", "medium"),
                ", ".join(issue.get("labels", [])),
            )

        console.print(table)
        console.print(f"\n  Project: [bold]{plan.get('project_name', 'N/A')}[/bold]")
        console.print(f"  Issues:  [bold]{len(plan['issues'])}[/bold]")

    # Save the plan
    output_path = DATA_DIR / "step2_plan.json"
    output_path.write_text(json.dumps(plan, indent=2))
    console.print(f"\n[green]✓[/green] Plan saved to [bold]{output_path}[/bold]")

    await session.destroy()
    await client.stop()

    return plan


def run():
    """Entry point for Step 2."""
    return asyncio.run(plan_tasks())
