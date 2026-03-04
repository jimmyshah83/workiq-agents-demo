"""Configuration management for the workiq-agents-demo app."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")

# Copilot SDK
COPILOT_MODEL = os.getenv("COPILOT_MODEL", "gpt-5")

# Work IQ
WORKIQ_TENANT_ID = os.getenv("WORKIQ_TENANT_ID", "")

# MCP server config for Work IQ (used by the Copilot CLI)
WORKIQ_MCP_CONFIG = {
    "mcpServers": {
        "workiq": {
            "command": "npx",
            "args": ["-y", "@microsoft/workiq", "--tenant-id", WORKIQ_TENANT_ID, "mcp"] if WORKIQ_TENANT_ID else ["-y", "@microsoft/workiq", "mcp"],
            "tools": ["*"],
        }
    }
}
