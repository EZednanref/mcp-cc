"""Wrapper CodeCarbon pour le suivi énergétique."""

import logging
import subprocess
from datetime import datetime
from codecarbon import EmissionsTracker

logger = logging.getLogger(__name__)


class CodeCarbonTracker:
    """Gère le cycle de vie d'une session de tracking CodeCarbon."""

    def __init__(self, project_name: str = "mcp-codecarbon"):
        self.project_name = project_name
        self._tracker: EmissionsTracker | None = None
        self._start_time: datetime | None = None

    @property
    def is_tracking(self) -> bool:
        return self._tracker is not None

    def start(self, measure_power_secs: int = 15, save_to_file: bool = False) -> dict:
        """Démarre le tracking. Si déjà actif, relance automatiquement."""
        if self.is_tracking:
            self.stop()  # auto-restart propre

        self._tracker = EmissionsTracker(
            project_name=self.project_name,
            measure_power_secs=measure_power_secs,
            save_to_file=save_to_file,
            logging_logger=logger,
        )
        self._tracker.start()
        self._start_time = datetime.now()

        return {
            "project_name": self.project_name,
            "start_time": self._start_time.isoformat(),
        }

    def stop(self) -> dict:
        """Arrête le tracking et retourne les métriques finales."""
        if not self.is_tracking:
            raise RuntimeError("Aucune session de tracking active")

        emissions = self._tracker.stop()
        data = self._tracker.final_emissions_data
        end_time = datetime.now()

        result = {
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": end_time.isoformat(),
            "duration_seconds": data.duration,
            "emissions_kg": emissions,
            "energy_consumed_kwh": data.energy_consumed,
            "cpu_energy_kwh": data.cpu_energy,
            "gpu_energy_kwh": data.gpu_energy,
            "ram_energy_kwh": data.ram_energy,
            "country_name": data.country_name,
            "country_iso_code": data.country_iso_code,
        }

        # Reset
        self._tracker = None
        self._start_time = None
        return result

    def status(self) -> dict:
        """Retourne l'état courant du tracker."""
        return {
            "is_tracking": self.is_tracking,
            "project_name": self.project_name,
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }

    def run_and_measure(self, command: str, measure_power_secs: int = 15) -> dict:
        """Exécute une commande shell et mesure son empreinte énergétique."""
        self.start(measure_power_secs=measure_power_secs)
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=300,
            )
            metrics = self.stop()
            # Ajouter la sortie de la commande (tronquée à 2000 chars)
            metrics["command"] = command
            metrics["returncode"] = proc.returncode
            metrics["stdout"] = (proc.stdout or "")[-2000:]
            metrics["stderr"] = (proc.stderr or "")[-2000:]
            return metrics
        except Exception as e:
            # Nettoyer en cas d'erreur
            if self.is_tracking:
                try:
                    self._tracker.stop()
                except Exception:
                    pass
                self._tracker = None
                self._start_time = None
            raise RuntimeError(f"Erreur lors de l'exécution: {e}") from e
