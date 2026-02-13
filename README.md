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
- uv

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

- at the root of the project, execute codecarbon login
then login to your codecarbon account, a credential file will be generated at the root.

## Run

From repository root:

```bash
uv run server.py
```

The server will start and be ready to receive MCP client connections from AI Agent like Claude Desktop.

## Connect to an AI Agent

### What is MCP?

MCP (Model Context Protocol) allows AI assistants to communicate with external tools and data sources. Your CodeCarbon server exposes its capabilities as MCP tools that AI agents can discover and use automatically.

### Connecting to Claude Code (CLI)

Claude Code is Anthropic's command-line interface that natively supports MCP servers.

1. **Add your MCP server**:

   Navigate to your project directory and run:
   ```bash
   cd C:\Users\YourName\Desktop\PFE\mcp-cc
   claude mcp add codecarbon -- uv run server.py
   ```

2. **Verify the connection**:
   ```bash
   claude mcp list
   ```

   You should see:
   ```
   codecarbon: uv run server.py - ✓ Connected
   ```

3. **Restart Claude Code** to load the MCP server

4. **Start using it**:

   Once connected, you can interact naturally:
   ```
   "List my CodeCarbon organizations"
   "What's the consumption of my bert-base experiment?"
   "Which model consumes the least with 90% accuracy minimum?"
   ```

### Connecting to Claude Desktop (GUI)

For Claude Desktop on Mac/Windows:

1. Open the Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server configuration:
   ```json
   {
     "mcpServers": {
       "codecarbon": {
         "command": "uv",
         "args": ["run", "server.py"],
         "cwd": "C:\\Users\\YourName\\Desktop\\PFE\\mcp-cc"
       }
     }
   }
   ```

3. Restart Claude Desktop

### How It Works

```
┌─────────────────┐
│   AI Agent      │  (Claude Code / Claude Desktop)
│  (Claude LLM)   │
└────────┬────────┘
         │ JSON-RPC over STDIO
         ▼
┌─────────────────┐
│  MCP Server     │  (server.py)
│  FastMCP        │  Exposes 8 tools
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│ CodeCarbon API  │  (api.codecarbon.io)
└─────────────────┘
```

The AI agent:
1. **Discovers** available tools on startup
2. **Interprets** your natural language request
3. **Calls** the appropriate MCP tool(s)
4. **Formats** the response in a readable way

All communication happens automatically - you just ask questions in natural language!

## MCP Tools

- `check_auth`
- `list_organizations`
- `list_projects`
- `list_experiments`
- `create_experiment` - Create a new experiment in a project
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

