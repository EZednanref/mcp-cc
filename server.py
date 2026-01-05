#!/usr/bin/env python3
"""
Serveur MCP pour CodeCarbon.

Ce module expose plusieurs outils MCP permettant de démarrer,
arrêter et consulter un suivi de consommation énergétique
via la bibliothèque CodeCarbon.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from mcp.server.fastmcp import FastMCP
from codecarbon import EmissionsTracker

# Initialisation du serveur MCP
mcp = FastMCP("codecarbon")

# Tracker global 
tracker: Optional[EmissionsTracker] = None
start_time: Optional[datetime] = None


@mcp.tool()
async def start_tracking(measure_power_secs: int = 15) -> Dict[str, Any]:
    """
    Démarre le s    uivi énergétique avec CodeCarbon.

    Args:
        measure_power_secs: Intervalle de mesure de la puissance (en secondes)

    Returns:
        Informations sur l'état du suivi
    """
    global tracker, start_time

    if tracker is not None:
        return {
            "status": "already_running",
            "message": "suivi est déjà en cours."
        }

    tracker = EmissionsTracker(
        project_name="mcp-codecarbon-tracking",
        measure_power_secs=measure_power_secs,
        log_level="info"
    )

    tracker.start()
    start_time = datetime.now()

    return {
        "status": "started",        
        "start_time": start_time.isoformat(),
        "project_name": tracker._project_name,
        "measurement_interval": measure_power_secs
    }


@mcp.tool()
async def stop_tracking() -> Dict[str, Any]:
    """
    Arrête le suivi énergétique et retourne les métriques finales.

    Returns:
        Résumé de la consommation énergétique et des émissions carbone
    """
    global tracker, start_time

    if tracker is None:
        raise RuntimeError("pas de suivi actif")

    emissions = tracker.stop()
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds() if start_time else 0

    tracker = None
    start_time = None

    return {
        "status": "stopped",
        "duration_seconds": round(duration, 2),
        "emissions_kg_co2": emissions
    }


@mcp.tool()
async def get_status() -> Dict[str, Any]:
    """
    Retourne l'état actuel du suivi énergétique.

    Returns:
        État du tracker (actif ou non)
    """
    if tracker is None:
        return {
            "status": "not_tracking"
        }

    return {
        "status": "tracking",
        "start_time": start_time.isoformat() if start_time else None
    }


@mcp.tool()
async def get_current_metrics() -> Dict[str, Any]:
    """
    Retourne des informations sur le suivi en cours
    sans arrêter le tracker.

    Returns:
        Informations temporelles sur le suivi
    """
    if tracker is None or start_time is None:
        raise RuntimeError("Aucun suivi actif")

    now = datetime.now()
    duration = (now - start_time).total_seconds()

    return {
        "status": "tracking",
        "start_time": start_time.isoformat(),
        "current_time": now.isoformat(),
        "duration_seconds": round(duration, 2)
    }


def main():
    """Lance le serveur MCP en mode stdio."""
    logging.info("Démarrage du serveur MCP...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
