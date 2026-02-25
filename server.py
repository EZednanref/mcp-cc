from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import logging

from mcp.server.fastmcp import FastMCP
from analysis import aggregate_run_summaries, select_lowest_consumption_experiment
from client import CodeCarbonApiClient

# Initialize the MCP server with the name "codecarbon-api"
mcp = FastMCP("codecarbon-api")


def _get_access_token_from_file() -> str:
    """
    Read the CodeCarbon API access token from a local credentials file.
    Raises an error if the file or token is missing, prompting the user to log in.
    Default location is credentials.json in the current working directory, created by `codecarbon login`.
    """
    cred_path = Path("credentials.json")
    if not cred_path.exists():
        # Raise error if the credentials file does not exist
        raise FileNotFoundError(
            f"No credentials file found at {cred_path}. Please run `codecarbon login` first."
        )
    # Open the credentials file and parse JSON
    with cred_path.open("r") as f:
        data = json.load(f)
    try:
        # Return the access token from the parsed data
        return data["tokens"]["access_token"]
    except KeyError:
        # Raise error if access token is missing
        raise ValueError(
            "No access_token found in credentials file. Run `codecarbon login` again."
        )


def _build_client() -> CodeCarbonApiClient:
    """
    Build and return a CodeCarbon API client configured with the access token.
    """
    base_url = "https://api.codecarbon.io"  # Default API URL
    access_token = _get_access_token_from_file()
    # Instantiate the API client with URL and token
    return CodeCarbonApiClient(base_url=base_url, access_token=access_token)


@mcp.tool()
def check_auth() -> dict[str, Any]:
    """Validate that MCP server credentials can access the CodeCarbon API."""
    return _build_client().check_auth()


@mcp.tool()
def list_organizations() -> list[dict[str, Any]]:
    """List organizations visible by the configured credentials."""
    return _build_client().list_organizations()


@mcp.tool()
def list_projects(organization_id: str) -> list[dict[str, Any]]:
    """List all projects under the specified organization."""
    return _build_client().list_projects(organization_id)


@mcp.tool()
def list_experiments(project_id: str) -> list[dict[str, Any]]:
    """List all experiments under the specified project."""
    return _build_client().list_experiments(project_id)


@mcp.tool()
def get_experiment_consumption(
    experiment_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Return aggregated consumption for a specific experiment, optionally
    filtering runs by a start and end date.
    """
    client = _build_client()
    # Fetch experiment metadata
    experiment = client.get_experiment(experiment_id)
    # Fetch all run summaries for the experiment
    run_summaries = client.get_experiment_run_summaries(
        experiment_id=experiment_id,
        start_date=start_date,
        end_date=end_date,
    )
    # Aggregate run summaries into totals
    totals = aggregate_run_summaries(run_summaries)
    return {
        "experiment": {
            "id": experiment.get("id"),
            "name": experiment.get("name"),
            "description": experiment.get("description"),
            "project_id": experiment.get("project_id"),
        },
        "window": {"start_date": start_date, "end_date": end_date},
        "totals": totals,
        "runs": run_summaries,
    }


@mcp.tool()
def get_experiment_consumption_by_name(
    project_id: str,
    experiment_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Find an experiment by exact or partial name in a project, then return its consumption.
    If multiple experiments match, returns a message listing matches.
    """
    client = _build_client()
    # List all experiments in the project
    experiments = client.list_experiments(project_id)
    lowered = experiment_name.strip().lower()
    # First try exact match
    exact = [exp for exp in experiments if exp.get("name", "").strip().lower() == lowered]
    # Fallback to partial match
    partial = [exp for exp in experiments if lowered in exp.get("name", "").strip().lower()]
    matches = exact or partial
    if not matches:
        # Return empty if no matches
        return {
            "message": f"No experiment found for name '{experiment_name}' in project {project_id}.",
            "matches": [],
        }
    if len(matches) > 1:
        # Return multiple matches warning
        return {
            "message": f"Multiple experiments match '{experiment_name}'.",
            "matches": [{"id": m.get("id"), "name": m.get("name")} for m in matches],
        }
    # If exactly one match, return its consumption
    return get_experiment_consumption(
        experiment_id=matches[0]["id"], start_date=start_date, end_date=end_date
    )


@mcp.tool()
def recommend_lowest_emission_experiment(
    project_id: str,
    min_accuracy: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Recommend the least carbon-emitting experiment in a project,
    optionally filtering by minimum accuracy.

    Accuracy is inferred from experiment name/description formatted as
    `accuracy=92.1` or `accuracy: 92.1%`.
    """
    client = _build_client()
    # Fetch experiment summaries for the project
    reports = client.get_project_experiment_summaries(
        project_id=project_id, start_date=start_date, end_date=end_date
    )
    # Select the experiment with lowest consumption that meets min_accuracy
    recommendation = select_lowest_consumption_experiment(
        experiment_reports=reports,
        min_accuracy=min_accuracy,
    )
    return {
        "project_id": project_id,
        "window": {"start_date": start_date, "end_date": end_date},
        "recommendation": recommendation,
        "experiments_considered": len(reports),
    }


@mcp.tool()
def create_experiment(
    project_id: str,
    name: str,
    description: str | None = None,
    timestamp: str | None = None,
    country_name: str | None = None,
    country_iso_code: str | None = None,
    region: str | None = None,
    on_cloud: bool = False,
    cloud_provider: str | None = None,
    cloud_region: str | None = None,
) -> dict[str, Any]:
    """
    Create a new experiment in a CodeCarbon project with optional metadata.
    """
    client = _build_client()
    return client.create_experiment(
        project_id=project_id,
        name=name,
        description=description,
        timestamp=timestamp,
        country_name=country_name,
        country_iso_code=country_iso_code,
        region=region,
        on_cloud=on_cloud,
        cloud_provider=cloud_provider,
        cloud_region=cloud_region,
    )


@mcp.tool()
def demo_prompt_scenarios() -> list[dict[str, str]]:
    """Return example prompts to demo the MCP with experiment data."""
    return [
        {
            "title": "Experiment Consumption",
            "prompt": "What is the consumption of my experiment bert-base-uncased-v1?",
            "tool_chain": "get_experiment_consumption_by_name",
        },
        {
            "title": "Comparison with Accuracy Constraint",
            "prompt": "Which model consumes the least with a minimum accuracy of 92%?",
            "tool_chain": "recommend_lowest_emission_experiment(min_accuracy=92)",
        },
        {
            "title": "Project Inventory",
            "prompt": "List the available experiments in Benoit's project.",
            "tool_chain": "list_experiments",
        },
        {
            "title": "Create a Simple Experiment",
            "prompt": "Create a new experiment named 'llama-3-8B-fine-tuned' with the description 'Fine-tuning for text classification' in my project",
            "tool_chain": "create_experiment",
        },
    ]


def main():
    """Start the MCP server using stdio transport."""
    logging.info("Starting MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
