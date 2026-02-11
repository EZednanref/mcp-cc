from __future__ import annotations

import re
from typing import Any


_ACCURACY_PATTERNS = (
    r"(?:accuracy|acc|precision|f1|score)\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*%?",
    r"(\d+(?:[.,]\d+)?)\s*%\s*(?:accuracy|acc|precision|f1|score)",
)

_MODEL_PATTERNS = (
    r"(?:model|model_name)\s*[:=]\s*([A-Za-z0-9._\-/]+)",
    r"\b(llama[0-9.\-a-zA-Z]*)\b",
    r"\b(mistral[0-9.\-a-zA-Z]*)\b",
)


def normalize_accuracy(value: float) -> float:
    """Normalize `90` -> `0.9` and keep `0.9` as-is."""
    if value > 1:
        return value / 100.0
    return value


def extract_accuracy(text: str | None) -> float | None:
    if not text:
        return None
    for pattern in _ACCURACY_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", ".")
            return normalize_accuracy(float(raw))
    return None


def extract_model_name(name: str | None, description: str | None) -> str | None:
    text = " ".join([x for x in (name, description) if x])
    if not text:
        return None
    for pattern in _MODEL_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return name


def aggregate_run_summaries(run_reports: list[dict[str, Any]]) -> dict[str, Any]:
    emissions = sum(float(item.get("emissions") or 0.0) for item in run_reports)
    energy_consumed = sum(
        float(item.get("energy_consumed") or 0.0) for item in run_reports
    )
    duration = sum(float(item.get("duration") or 0.0) for item in run_reports)
    return {
        "run_count": len(run_reports),
        "emissions_kg_co2e": emissions,
        "energy_kwh": energy_consumed,
        "duration_seconds": duration,
    }


def select_lowest_consumption_experiment(
    experiment_reports: list[dict[str, Any]],
    min_accuracy: float | None = None,
) -> dict[str, Any]:
    normalized_threshold = (
        normalize_accuracy(min_accuracy) if min_accuracy is not None else None
    )

    candidates = []
    for report in experiment_reports:
        accuracy = extract_accuracy(
            f"{report.get('name', '')} {report.get('description', '')}"
        )
        emissions = float(report.get("emissions") or 0.0)
        candidate = {
            "experiment_id": report.get("experiment_id"),
            "name": report.get("name"),
            "description": report.get("description"),
            "model": extract_model_name(report.get("name"), report.get("description")),
            "accuracy": accuracy,
            "emissions_kg_co2e": emissions,
            "energy_kwh": float(report.get("energy_consumed") or 0.0),
            "duration_seconds": float(report.get("duration") or 0.0),
        }
        if normalized_threshold is None or (
            accuracy is not None and accuracy >= normalized_threshold
        ):
            candidates.append(candidate)

    if not candidates:
        return {
            "selected": None,
            "min_accuracy": normalized_threshold,
            "candidate_count": 0,
            "message": "No experiment matches the requested minimum accuracy.",
        }

    selected = min(
        candidates,
        key=lambda c: (
            c["emissions_kg_co2e"],
            c["energy_kwh"],
            c["duration_seconds"],
        ),
    )
    return {
        "selected": selected,
        "min_accuracy": normalized_threshold,
        "candidate_count": len(candidates),
    }

