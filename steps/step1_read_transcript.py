"""Step 1: Read meeting transcripts from Microsoft 365 via Work IQ.

Calls the Work IQ CLI directly (npx @microsoft/workiq) to query your
M365 data, then saves the result for subsequent pipeline steps.

Run:  python main.py step1
      python main.py step1 --query "yesterday's standup"
      python main.py step1 --list     # list recent meetings first, then pick one
"""

import json
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from config import DATA_DIR, WORKIQ_TENANT_ID

console = Console()


# ---------------------------------------------------------------------------
# Work IQ helper – calls the CLI directly (most reliable auth path)
# ---------------------------------------------------------------------------

def _workiq_ask(question: str) -> str:
    """Run ``npx -y @microsoft/workiq ask -q <question>`` and return stdout."""
    cmd = ["npx", "-y", "@microsoft/workiq"]
    if WORKIQ_TENANT_ID:
        cmd += ["--tenant-id", WORKIQ_TENANT_ID]
    cmd += ["ask", "-q", question]

    console.print(f"[dim]  Running: {' '.join(cmd[:6])}…[/dim]")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        err = result.stderr.strip()
        console.print(f"[red]  ✗ Work IQ error: {err}[/red]")
        raise RuntimeError(f"Work IQ failed (exit {result.returncode}): {err}")

    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def list_recent_meetings() -> str:
    """Ask Work IQ to list recent meetings."""
    console.print("[dim]Fetching recent meetings from Work IQ…[/dim]\n")
    meetings = _workiq_ask(
        "List my meetings from the past 7 days. "
        "For each meeting show a number, the title, date/time, and duration. "
        "Format as a numbered list."
    )
    console.print(meetings)
    return meetings


def get_transcript_for_meeting(meeting_description: str) -> str:
    """Retrieve transcript / recap for a specific meeting."""
    console.print("\n[dim]Fetching transcript…[/dim]\n")
    transcript = _workiq_ask(
        f"Get the full transcript or detailed recap of this meeting: "
        f"{meeting_description}. "
        f"Include attendees, what was discussed, decisions made, and action items."
    )
    console.print(transcript)
    return transcript


def read_meeting_transcript(
    meeting_query: str | None = None,
    list_first: bool = False,
) -> dict:
    """Query Work IQ for meeting transcripts.

    Args:
        meeting_query: Natural-language query for the meeting, e.g.
            "my most recent team meeting" or "yesterday's standup".
        list_first: If True, list recent meetings and let the user pick one.

    Returns:
        dict with 'transcript' and 'meeting_query' keys.
    """
    console.print(
        Panel("[bold cyan]Step 1:[/] Reading meeting transcript", subtitle="Work IQ")
    )

    if list_first:
        # Phase 1 – list meetings
        meetings_text = list_recent_meetings()
        console.print()

        selection = Prompt.ask(
            "[bold]Enter the number of the meeting you want[/bold], or describe it",
            default="1",
        )
        meeting_query = f"meeting number {selection} from this list:\n{meetings_text}"
        console.print(f"\n  Selected: [italic]{selection}[/italic]")

    elif meeting_query is None:
        meeting_query = "my most recent team meeting"

    console.print(f"  Query: [italic]{meeting_query}[/italic]\n")

    # Phase 2 – get transcript
    transcript = get_transcript_for_meeting(meeting_query)

    # Persist for downstream steps
    result = {
        "meeting_query": meeting_query,
        "transcript": transcript,
    }
    output_path = DATA_DIR / "step1_transcript.json"
    output_path.write_text(json.dumps(result, indent=2))
    console.print(f"\n[green]✓[/green] Transcript saved to [bold]{output_path}[/bold]")

    return result


def run(meeting_query: str | None = None, list_first: bool = False):
    """Entry point for Step 1."""
    return read_meeting_transcript(meeting_query, list_first=list_first)
