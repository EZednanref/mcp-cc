import csv
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from codecarbon import EmissionsTracker
from codecarbon.output_methods.emissions_data import EmissionsData
from mcp.server.fastmcp import FastMCP


@dataclass
class RunState:
    tracker: EmissionsTracker
    started_at: str
    output_dir: str
    output_file: str


class LocalRunManager:
    def __init__(self) -> None:
        self._active: Optional[RunState] = None
        self._last_output: Optional[Tuple[str, str]] = None

    def start(
        self,
        project_name: str = "codecarbon",
        experiment_id: Optional[str] = None,
        output_dir: str = ".",
        output_file: str = "emissions.csv",
        tracking_mode: str = "machine",
    ) -> Dict[str, Any]:
        if self._active is not None:
            raise RuntimeError("A measurement is already running.")
        if tracking_mode not in {"machine", "process"}:
            raise ValueError("tracking_mode must be 'machine' or 'process'.")
        if not os.path.isdir(output_dir):
            raise ValueError(f"output_dir does not exist: {output_dir}")

        tracker = EmissionsTracker(
            project_name=project_name,
            experiment_id=experiment_id,
            output_dir=output_dir,
            output_file=output_file,
            save_to_file=True,
            save_to_api=False,
            tracking_mode=tracking_mode,
        )

        tracker.start()

        started_at = datetime.now(timezone.utc).isoformat()
        self._active = RunState(
            tracker=tracker,
            started_at=started_at,
            output_dir=output_dir,
            output_file=output_file,
        )
        self._last_output = (output_dir, output_file)

        return {
            "run_id": str(tracker.run_id),
            "started_at": started_at,
            "output_dir": output_dir,
            "output_file": output_file,
        }

    def stop(self) -> Dict[str, Any]:
        if self._active is None:
            raise RuntimeError("No active measurement to stop.")

        tracker = self._active.tracker
        emissions_kg = tracker.stop()
        final_data = tracker.final_emissions_data

        result = {
            "run_id": str(tracker.run_id),
            "emissions_kg": emissions_kg,
            "data": _emissions_data_to_dict(final_data),
        }

        self._last_output = (self._active.output_dir, self._active.output_file)
        self._active = None

        return result

    def get_last_run(
        self, output_dir: Optional[str], output_file: Optional[str]
    ) -> Dict[str, Any]:
        path = self._resolve_output_path(output_dir, output_file)
        rows = _read_csv_rows(path)
        if not rows:
            return {"output_path": path, "last_run": None}
        return {"output_path": path, "last_run": rows[-1]}

    def list_recent_runs(
        self, limit: int, output_dir: Optional[str], output_file: Optional[str]
    ) -> Dict[str, Any]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        path = self._resolve_output_path(output_dir, output_file)
        rows = _read_csv_rows(path, max_rows=limit)
        return {"output_path": path, "runs": rows}

    def _resolve_output_path(
        self, output_dir: Optional[str], output_file: Optional[str]
    ) -> str:
        if output_dir is None or output_file is None:
            if self._last_output is not None:
                default_dir, default_file = self._last_output
            else:
                default_dir, default_file = ".", "emissions.csv"
            output_dir = output_dir or default_dir
            output_file = output_file or default_file
        return os.path.join(output_dir, output_file)


def _emissions_data_to_dict(data: Optional[EmissionsData]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    return dict(data.values)


def _read_csv_rows(path: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []

    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if max_rows is None:
            for row in reader:
                rows.append(row)
            return rows

        for row in reader:
            rows.append(row)
            if len(rows) > max_rows:
                rows.pop(0)
        return rows


mcp = FastMCP("codecarbon-local")
_manager = LocalRunManager()


@mcp.tool()
def start_measurement(
    project_name: str = "codecarbon",
    experiment_id: Optional[str] = None,
    output_dir: str = ".",
    output_file: str = "emissions.csv",
    tracking_mode: str = "machine",
) -> Dict[str, Any]:
    """
    Start a local CodeCarbon measurement.
    """
    return _manager.start(
        project_name=project_name,
        experiment_id=experiment_id,
        output_dir=output_dir,
        output_file=output_file,
        tracking_mode=tracking_mode,
    )


@mcp.tool()
def stop_measurement() -> Dict[str, Any]:
    """
    Stop the current local measurement.
    """
    return _manager.stop()


@mcp.tool()
def get_last_run(
    output_dir: Optional[str] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return the last run from emissions.csv.
    """
    return _manager.get_last_run(output_dir, output_file)


@mcp.tool()
def list_recent_runs(
    limit: int = 10,
    output_dir: Optional[str] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List recent runs from emissions.csv.
    """
    return _manager.list_recent_runs(limit, output_dir, output_file)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
