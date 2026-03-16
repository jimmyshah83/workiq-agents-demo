"""Step 2: Analyze the meeting transcript and plan implementation tasks.

Uses the GitHub Copilot SDK to break down the meeting transcript
into a structured plan of GitHub issues with descriptions.

Run:  python main.py step2
"""

import asyncio
import json
import re
from pathlib import Path

from copilot import CopilotClient, PermissionHandler
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

CRITICAL RULES:
- Return ONLY the JSON object above — no markdown fencing, no explanation, no extra text.
- Do NOT use any tools or read any files. Work ONLY from the transcript provided.
- Your entire response must be valid JSON and nothing else.\
"""


def _extract_json_plan(text: str) -> dict | None:
    """Try multiple strategies to extract a JSON plan from the response."""
    stripped = text.strip()

    # Strategy 1: entire response is JSON
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2: JSON wrapped in markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", stripped, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: find the outermost { ... } containing "issues"
    for match in re.finditer(r"\{", stripped):
        start = match.start()
        depth = 0
        for i in range(start, len(stripped)):
            if stripped[i] == "{":
                depth += 1
            elif stripped[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = stripped[start : i + 1]
                    if '"issues"' in candidate:
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            pass
                    break

    return None


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

    import os
    cli_env = {k: v for k, v in os.environ.items()
               if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    client = CopilotClient({"use_logged_in_user": True, "env": cli_env})
    await client.start()

    session = await client.create_session({
        "model": COPILOT_MODEL,
        "on_permission_request": PermissionHandler.approve_all,
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
    plan = _extract_json_plan(full_response)

    if plan is None:
        # Retry: ask the model to return just the JSON
        console.print("[yellow]Retrying:[/yellow] asking for JSON-only response...\n")
        collected_response.clear()
        done.clear()
        await session.send({
            "prompt": (
                "Your previous response could not be parsed as JSON. "
                "Please respond with ONLY the raw JSON object — no markdown, "
                "no explanation, no code fences. Just the JSON."
            ),
        })
        await done.wait()
        retry_response = "".join(collected_response)
        plan = _extract_json_plan(retry_response)

    if plan is None:
        console.print("[red]✗[/red] Could not extract JSON plan from Copilot response.")
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
