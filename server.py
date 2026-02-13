from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import logging

from mcp.server.fastmcp import FastMCP
from analysis import aggregate_run_summaries, select_lowest_consumption_experiment
from client import CodeCarbonApiClient

mcp = FastMCP("codecarbon-api")


def _get_access_token_from_file() -> str:
    """
    Read the CodeCarbon API access token from a local credentials file.
    Raises an error if the file or token is missing, prompting the user to log in.
    default location is .credentials.json in the current working directory, created by `codecarbon login`.
    """
    cred_path = Path(".credentials.json")
    if not cred_path.exists():
        raise FileNotFoundError(
            f"No credentials file found at {cred_path}. Please run `codecarbon login` first."
        )
    with cred_path.open("r") as f:
        data = json.load(f)
    try:
        return data["tokens"]["access_token"]
    except KeyError:
        raise ValueError(
            "No access_token found in credentials file. Run `codecarbon login` again."
        )


def _build_client() -> CodeCarbonApiClient:
    """
    Crée un client CodeCarbonApiClient configuré avec l'API et le token d'accès.
    """
    base_url = "https://api.codecarbon.io"  # URL par défaut de l'API
    access_token = _get_access_token_from_file()
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
    """List projects under one organization."""
    return _build_client().list_projects(organization_id)


@mcp.tool()
def list_experiments(project_id: str) -> list[dict[str, Any]]:
    """List experiments under one project."""
    return _build_client().list_experiments(project_id)


@mcp.tool()
def get_experiment_consumption(
    experiment_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Return aggregated consumption for one experiment from run summaries."""
    client = _build_client()
    experiment = client.get_experiment(experiment_id)
    run_summaries = client.get_experiment_run_summaries(
        experiment_id=experiment_id,
        start_date=start_date,
        end_date=end_date,
    )
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
    """Find an experiment by exact/partial name in a project, then return consumption."""
    client = _build_client()
    experiments = client.list_experiments(project_id)
    lowered = experiment_name.strip().lower()
    exact = [exp for exp in experiments if exp.get("name", "").strip().lower() == lowered]
    partial = [
        exp
        for exp in experiments
        if lowered in exp.get("name", "").strip().lower()
    ]
    matches = exact or partial
    if not matches:
        return {
            "message": f"No experiment found for name '{experiment_name}' in project {project_id}.",
            "matches": [],
        }
    if len(matches) > 1:
        return {
            "message": f"Multiple experiments match '{experiment_name}'.",
            "matches": [{"id": m.get("id"), "name": m.get("name")} for m in matches],
        }
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
    Recommend the least emitting experiment in a project, optionally with min accuracy.

    Note:
    Accuracy is inferred from experiment `name`/`description` when encoded as
    `accuracy=92.1` or `accuracy: 92.1%`.
    """
    client = _build_client()
    reports = client.get_project_experiment_summaries(
        project_id=project_id, start_date=start_date, end_date=end_date
    )
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
    Create a new experiment in a CodeCarbon project.

    Args:
        project_id: ID of the project to create the experiment in
        name: Name of the experiment (required)
        description: Optional description of the experiment
        timestamp: ISO 8601 timestamp (e.g., "2021-04-04T08:43:00+02:00")
        country_name: Country where the experiment runs (e.g., "France")
        country_iso_code: ISO country code (e.g., "FRA")
        region: Region name (e.g., "france")
        on_cloud: Whether the experiment runs on cloud infrastructure
        cloud_provider: Cloud provider name (e.g., "aws", "gcp", "azure")
        cloud_region: Cloud region identifier (e.g., "eu-west-1a")

    Returns:
        The created experiment data
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
    """Return practical prompt examples to demo this MCP with Benoit's experiment data."""
    return [
        {
            "title": "Consommation d'une expérience",
            "prompt": "Quelle est la consommation de mon expérience bert-base-uncased-v1 ?",
            "tool_chain": "get_experiment_consumption_by_name",
        },
        {
            "title": "Comparaison avec contrainte de précision",
            "prompt": "Quel modèle consomme le moins avec une précision minimale de 92% ?",
            "tool_chain": "recommend_lowest_emission_experiment(min_accuracy=92)",
        },
        {
            "title": "Inventaire projet",
            "prompt": "Liste les expériences disponibles du projet de Benoit.",
            "tool_chain": "list_experiments",
        },
        {
            "title": "Créer une expérience simple",
            "prompt": "Crée une nouvelle expérience nommée 'llama-3-8B-fine-tuned' avec la description 'Fine-tuning pour classification de texte' dans mon projet",
            "tool_chain": "create_experiment",
        },

    ]

def main():
    logging.info("Starting MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
