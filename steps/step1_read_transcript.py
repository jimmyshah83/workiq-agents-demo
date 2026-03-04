"""Step 1: Read meeting transcripts from Microsoft 365 via Work IQ MCP server.

Uses the GitHub Copilot SDK to connect to Work IQ and retrieve
meeting transcripts for your team.

Run:  python main.py step1
"""

import asyncio
import json
from pathlib import Path

from copilot import CopilotClient
from rich.console import Console
from rich.panel import Panel

from config import COPILOT_MODEL, DATA_DIR

console = Console()


async def read_meeting_transcript(meeting_query: str | None = None) -> dict:
    """Query Work IQ for meeting transcripts via the Copilot SDK.

    The Copilot CLI must have the Work IQ MCP server plugin installed:
        /plugin marketplace add github/copilot-plugins
        /plugin install workiq@copilot-plugins

    Args:
        meeting_query: Natural language query for the meeting, e.g.
            "my most recent team meeting" or "yesterday's standup".
            Defaults to asking for recent meetings.

    Returns:
        dict with 'transcript' (str) and 'meeting_info' (str) keys.
    """
    if meeting_query is None:
        meeting_query = "my most recent team meeting"

    console.print(Panel(f"[bold cyan]Step 1:[/] Reading meeting transcript", subtitle="Work IQ + Copilot SDK"))
    console.print(f"  Query: [italic]{meeting_query}[/italic]\n")

    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": COPILOT_MODEL,
        "streaming": True,
    })

    collected_response = []
    done = asyncio.Event()

    def on_event(event):
        event_type = event.type.value if hasattr(event.type, "value") else str(event.type)

        if event_type == "assistant.message_delta":
            delta = event.data.delta_content or ""
            console.print(delta, end="", highlight=False)
            collected_response.append(delta)
        elif event_type == "assistant.message":
            if not collected_response:
                collected_response.append(event.data.content or "")
        elif event_type == "session.idle":
            done.set()

    session.on(on_event)

    prompt = f"""Using Work IQ, retrieve the transcript from {meeting_query}.

Return the full meeting transcript including:
- Meeting title/subject
- Date and time
- Attendees/participants
- The complete transcript of what was discussed

If there are action items or decisions mentioned, highlight those.
Format the output clearly."""

    console.print("[dim]Querying Work IQ for meeting transcript...[/dim]\n")
    await session.send({"prompt": prompt})
    await done.wait()

    full_response = "".join(collected_response)
    console.print()  # newline after streaming

    # Save the transcript to disk for subsequent steps
    result = {
        "meeting_query": meeting_query,
        "transcript": full_response,
    }

    output_path = DATA_DIR / "step1_transcript.json"
    output_path.write_text(json.dumps(result, indent=2))
    console.print(f"\n[green]✓[/green] Transcript saved to [bold]{output_path}[/bold]")

    await session.destroy()
    await client.stop()

    return result


def run(meeting_query: str | None = None):
    """Entry point for Step 1."""
    return asyncio.run(read_meeting_transcript(meeting_query))
