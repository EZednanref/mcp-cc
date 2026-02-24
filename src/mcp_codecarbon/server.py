"""Serveur MCP pour le tracking énergétique CodeCarbon."""

import logging
from mcp.server.fastmcp import FastMCP
from .tracker import CodeCarbonTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance unique du tracker et du serveur
tracker = CodeCarbonTracker()
mcp = FastMCP("mcp-codecarbon")


@mcp.tool()
async def start_tracking(measure_power_secs: int = 15, save_to_file: bool = False) -> dict:
    """Démarre le suivi énergétique (CPU/GPU/RAM).

    Si un suivi est déjà actif, il est arrêté et un nouveau commence.
    Mesure la consommation de la machine entière entre start et stop.

    Args:
        measure_power_secs: Intervalle de mesure en secondes (défaut: 15)
        save_to_file: Sauvegarder les résultats dans un CSV (défaut: False)
    """
    return tracker.start(
        measure_power_secs=measure_power_secs,
        save_to_file=save_to_file,
    )


@mcp.tool()
async def stop_tracking() -> dict:
    """Arrête le suivi et retourne les métriques finales.

    Retourne: énergie totale/CPU/GPU/RAM (kWh), émissions CO2 (kg), durée, localisation.
    """
    return tracker.stop()


@mcp.tool()
async def get_status() -> dict:
    """Vérifie si un suivi énergétique est en cours."""
    return tracker.status()


@mcp.tool()
async def run_and_measure(command: str, measure_power_secs: int = 15) -> dict:
    """Exécute une commande shell et mesure son empreinte énergétique.

    C'est l'outil principal : il lance la commande, mesure la consommation
    pendant son exécution, et retourne les métriques + la sortie de la commande.

    Args:
        command: Commande shell à exécuter (ex: 'python3 mon_script.py')
        measure_power_secs: Intervalle de mesure en secondes (défaut: 15)
    """
    return tracker.run_and_measure(
        command=command,
        measure_power_secs=measure_power_secs,
    )


def main():
    """Point d'entrée — lance le serveur MCP en mode stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
