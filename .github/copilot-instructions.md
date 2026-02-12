<!-- Copilot / AI agent instructions for the CodeCarbon MCP server -->
# Copilot instructions — CodeCarbon MCP server

This repository implements an MCP server that exposes CodeCarbon API capabilities to LLMs. The guidance below focuses on patterns and shortcuts an AI coding agent should know to be productive immediately.

- **Big picture:** This is an MCP tool wrapper around the CodeCarbon REST API. The key responsibilities are: calling the API (`client.py`), aggregating and interpreting run summaries (`analysis.py`), and exposing MCP tools via `server.py`.

- **Primary files:**
  - **Server / MCP entrypoints:** [server.py](server.py#L1-L200) — defines MCP tools and the `main()` runner.
  - **API client:** [client.py](client.py#L1-L200) — thin HTTP wrapper using `requests`, raises `CodeCarbonApiError` on HTTP >=400.
  - **Aggregation & heuristics:** [analysis.py](analysis.py#L1-L200) — accuracy/model extraction, normalization and selection logic.
  - **Project metadata / requirements:** [pyproject.toml](pyproject.toml#L1-L40) and [requirements.txt](requirements.txt#L1-L120).

- **Run / dev workflow (what actually works here):**
  - Preferred setup: install editable package and run the package entrypoint (recommended by README):

```
pip install -e .
python -m carbonserver.mcp.server
```

  - Quick dev run from repo root (this repo contains top-level modules):

```
python -m server          # runs server.py main() when present
```

- **Environment variables:** `CODECARBON_API_URL`, `CODECARBON_API_TOKEN`, `CODECARBON_ACCESS_TOKEN`. The client prefers `CODECARBON_API_TOKEN` and falls back to `CODECARBON_ACCESS_TOKEN` (see [server.py](server.py#L1-L80)).

- **MCP tools exposed:** see [server.py tool definitions](server.py#L1-L200). Notable tools:
  - `check_auth`, `list_organizations`, `list_projects`, `list_experiments`
  - `get_experiment_consumption`, `get_experiment_consumption_by_name`
  - `recommend_lowest_emission_experiment` — supports `min_accuracy` filtering (accuracy is inferred from name/description).

- **Accuracy & model heuristics:** `analysis.py` contains the exact regexes and normalization logic used by the server:
  - Accuracy parsing patterns are in `_ACCURACY_PATTERNS` and support formats like `accuracy=92.4` or `92.4% accuracy` (see [analysis.py](analysis.py#L1-L140)).
  - Model name extraction patterns are in `_MODEL_PATTERNS` and include common tokens (e.g., `llama...`, `mistral...`).
  - `normalize_accuracy()` converts `92` -> `0.92` and keeps `0.92` as-is; comparison logic uses normalized 0..1 values.

- **HTTP & error behavior:** `client.py` sets `x-api-token` when `CODECARBON_API_TOKEN` is present, otherwise uses `Authorization: Bearer <token>` when `CODECARBON_ACCESS_TOKEN` is set. All non-2xx responses raise `CodeCarbonApiError` (see [client.py](client.py#L1-L200)).

- **Patterns agents should follow when changing code:**
  - Keep public MCP tool signatures simple and serializable (tools return JSON-serializable structures).
  - New heuristics should be added to `analysis.py` and kept pure (input -> output) so tests can call them directly.
  - Client HTTP tweaks (timeouts, headers) belong in `client.py`.

- **Tests and local verification:** `pytest` is available in dependencies. Unit-test `analysis.py` functions (accuracy/model parsing and selection) first — they are deterministic and have no external dependencies.

- **Python runtime:** The project requests Python 3.12 in `pyproject.toml` — use a matching interpreter for local runs and CI.

- **What to avoid / known limitations:**
  - Accuracy is currently inferred from free-text fields; do not assume a structured `accuracy` field exists in API responses.
  - The README recommends running from an installed package layout (`carbonserver...`); if editing top-level modules directly, `python -m server` is a convenient shortcut.

- **When editing or adding tools:**
  - Update the MCP tool list in `server.py` and keep tooling logic thin — heavy lifting belongs in `analysis.py` or `client.py`.
  - Add or update unit tests for `analysis.py` patterns and `client.py` error handling.

If any of the above sections are unclear or you'd like me to add quick unit tests or CI steps, tell me which area to expand and I will iterate.
