from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from analysis import (
    aggregate_run_summaries,
    select_lowest_consumption_experiment,
)
from client import CodeCarbonApiClient

mcp = FastMCP("codecarbon-api")


def _build_client() -> CodeCarbonApiClient:
    base_url = os.getenv("CODECARBON_API_URL", "https://api.codecarbon.io")
    api_token = os.getenv("CODECARBON_API_TOKEN")
    access_token = os.getenv("CODECARBON_ACCESS_TOKEN")
    return CodeCarbonApiClient(
        base_url=base_url, api_token=api_token, access_token=access_token
    )


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
    ]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

