# CodeCarbon API MCP Server

This MCP server exposes CodeCarbon API capabilities to LLM clients through MCP tools.

It is designed for a setup where the server runs with Benoit's credentials and queries
experiment records directly from the official API.

## Features

- Read organizations, projects, and experiments from CodeCarbon API.
- Compute experiment consumption from run summaries.
- Recommend the least emitting experiment with an optional minimum accuracy.
- Provide demo prompt scenarios for Friday's presentation.

## Requirements

- Python 3.12 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-cc
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Before running the server, set your CodeCarbon API credentials:

- `CODECARBON_API_URL`: API base URL (default: `https://api.codecarbon.io`)
- `CODECARBON_API_TOKEN`: Project/API token (preferred when available)
- `CODECARBON_ACCESS_TOKEN`: Bearer token fallback

Use one of `CODECARBON_API_TOKEN` or `CODECARBON_ACCESS_TOKEN`.

### Setting Environment Variables

**On macOS/Linux:**
```bash
export CODECARBON_API_TOKEN="your_token_here"
export CODECARBON_API_URL="https://api.codecarbon.io"
```

**On Windows (PowerShell):**
```powershell
$env:CODECARBON_API_TOKEN="your_token_here"
$env:CODECARBON_API_URL="https://api.codecarbon.io"
```

**On Windows (Command Prompt):**
```cmd
set CODECARBON_API_TOKEN=your_token_here
set CODECARBON_API_URL=https://api.codecarbon.io
```

## Run

From repository root:

```bash
python3 -m server
```

The server will start and be ready to receive MCP client connections.

## MCP Tools

- `check_auth`
- `list_organizations`
- `list_projects`
- `list_experiments`
- `get_experiment_consumption`
- `get_experiment_consumption_by_name`
- `recommend_lowest_emission_experiment`
- `demo_prompt_scenarios`

## Accuracy Constraint Notes

The `recommend_lowest_emission_experiment` tool can enforce `min_accuracy`, but the API
does not expose a dedicated accuracy field today. The server infers accuracy from
experiment `name` or `description` when formatted like:

- `accuracy=92.4`
- `accuracy: 92.4%`

For production usage, prefer storing accuracy in a structured field and exposing it via API.

