# Work IQ → GitHub Copilot Agent Pipeline

Transform meeting transcripts into implemented code — automatically.

This app reads your team's meeting transcript from Microsoft 365 via **Work IQ**,
uses the **GitHub Copilot SDK** to plan implementation tasks, creates a GitHub repo
with issues, and assigns the **Copilot coding agent** to execute each one, producing
PRs for your review.

```
Meeting Transcript ──→ Plan ──→ Repo ──→ Issues ──→ Coding Agent ──→ PRs
     (Work IQ)      (Copilot SDK)  (GitHub API)       (copilot-swe-agent)
```

## Prerequisites

1. **Python 3.11+**
2. **GitHub Copilot CLI** — [Install guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
3. **GitHub Copilot subscription** (Pro, Pro+, Business, or Enterprise)
4. **Work IQ MCP server** — requires a Microsoft 365 subscription with Microsoft 365 Copilot and tenant admin approval. [Details →](https://github.com/microsoft/work-iq-mcp)
5. **Node.js 18+** — required for the Work IQ MCP server (`npx`)
6. **GitHub Personal Access Token** — with `repo` scope

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USER/workiq-agents-demo.git
cd workiq-agents-demo

# 2. Install Python dependencies
pip install -e .

# 3. Configure environment variables
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN

# 4. Install the Work IQ plugin in Copilot CLI
copilot
/plugin marketplace add github/copilot-plugins
/plugin install workiq@copilot-plugins

# 5. Sign in to Work IQ (first time only)
npx -y @microsoft/workiq accept-eula
```

## Usage

Run each step independently to see results at each stage:

### Step 1: Read Meeting Transcript

```bash
python main.py step1
# Or specify a specific meeting:
python main.py step1 --query "yesterday's standup"
```

Connects to Work IQ via the Copilot SDK to retrieve and display a meeting transcript from your Microsoft 365 account. Saves the transcript to `data/step1_transcript.json`.

### Step 2: Plan Implementation Tasks

```bash
python main.py step2
```

Sends the transcript to the Copilot SDK, which analyzes discussions and produces a structured plan of GitHub issues with titles, descriptions, labels, and priorities. Saves the plan to `data/step2_plan.json`.

### Step 3: Create GitHub Repository

```bash
python main.py step3
```

Creates a new GitHub repository based on the project name from the plan. Saves repo metadata to `data/step3_repo.json`.

### Step 4: Create GitHub Issues

```bash
python main.py step4
```

Creates GitHub issues in the repo from the planned tasks, with labels and detailed descriptions. Saves issue info to `data/step4_issues.json`.

### Step 5: Assign Copilot Coding Agent

```bash
python main.py step5
```

Assigns `copilot-swe-agent[bot]` to each issue via the GitHub REST API. The coding agent begins working on each issue autonomously, creating branches and implementing the code.

### Step 6: Review Pull Requests

```bash
python main.py step6
```

Lists all pull requests in the repo, highlighting those created by the Copilot coding agent. Shows which PRs are awaiting your review.

### Run All Steps

```bash
python main.py all
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Work IQ MCP   │────→│  Copilot SDK     │────→│  GitHub REST API │
│  (M365 data)    │     │  (planning)      │     │  (repo/issues)   │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │ Copilot Coding   │
                                                │ Agent (PRs)      │
                                                └──────────────────┘
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Work IQ | MCP Server (`@microsoft/workiq`) | Access M365 meeting transcripts |
| Copilot SDK | `github-copilot-sdk` (Python) | AI-powered planning via Copilot CLI |
| GitHub API | PyGithub + REST API | Create repos, issues, assign agents |
| Coding Agent | `copilot-swe-agent[bot]` | Autonomous code implementation |

## Project Structure

```
workiq-agents-demo/
├── main.py                          # CLI entry point
├── config.py                        # Configuration & env vars
├── pyproject.toml                   # Python project config
├── mcp_config.json                  # Work IQ MCP server config
├── .env.example                     # Environment variables template
├── steps/
│   ├── step1_read_transcript.py     # Read meeting transcript via Work IQ
│   ├── step2_plan_tasks.py          # Plan tasks with Copilot SDK
│   ├── step3_create_repo.py         # Create GitHub repository
│   ├── step4_create_issues.py       # Create issues from plan
│   ├── step5_assign_agents.py       # Assign Copilot coding agent
│   └── step6_review_prs.py          # Monitor PRs for review
└── data/                            # Intermediate results (gitignored)
    ├── step1_transcript.json
    ├── step2_plan.json
    ├── step3_repo.json
    ├── step4_issues.json
    ├── step5_assignments.json
    └── step6_prs.json
```

## References

- [Work IQ Blog Post](https://developer.microsoft.com/blog/bringing-work-context-to-your-code-in-github-copilot)
- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [Work IQ MCP Server](https://github.com/microsoft/work-iq-mcp)
- [Copilot Coding Agent Docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr)
