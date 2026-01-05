"""
CodeCarbon wrapper module for energy and carbon tracking.

This module provides a clean interface to CodeCarbon's tracking capabilities,
designed to work without code instrumentation and provide metrics on demand.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from codecarbon import EmissionsTracker

logger = logging.getLogger(__name__)


class CodeCarbonTracker:
    """
    Wrapper class for CodeCarbon energy and carbon tracking.
    
    This class manages the lifecycle of energy tracking sessions and provides
    methods to start, stop, and retrieve metrics without requiring code instrumentation.
    """

    def __init__(self, project_name: str = "mcp-codecarbon-tracking"):
        """
        Initialize the CodeCarbon tracker.
        
        Args:
            project_name: Name of the project for tracking purposes
        """
        self.project_name = project_name
        self._tracker: Optional[EmissionsTracker] = None
        self._is_tracking = False
        self._start_time: Optional[datetime] = None
        logger.info(f"Initialized CodeCarbonTracker for project: {project_name}")

    def start_tracking(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Start energy and carbon tracking.
        
        Args:
            **kwargs: Additional parameters to pass to EmissionsTracker
            
        Returns:
            Dict containing status and start time
            
        Raises:
            RuntimeError: If tracking is already active
        """
        if self._is_tracking:
            error_msg = "Tracking is already active"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Create tracker with optional custom parameters
            tracker_kwargs = {
                "project_name": self.project_name,
                "measure_power_secs": kwargs.get("measure_power_secs", 15),
                "save_to_file": kwargs.get("save_to_file", False),
                "logging_logger": logger,
            }
            
            self._tracker = EmissionsTracker(**tracker_kwargs)
            self._tracker.start()
            self._is_tracking = True
            self._start_time = datetime.now()
            
            result = {
                "status": "started",
                "start_time": self._start_time.isoformat(),
                "project_name": self.project_name,
            }
            logger.info(f"Started tracking: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start tracking: {e}", exc_info=True)
            raise RuntimeError(f"Failed to start tracking: {e}") from e

    def stop_tracking(self) -> Dict[str, Any]:
        """
        Stop energy and carbon tracking and return final metrics.
        
        Returns:
            Dict containing final metrics and tracking information
            
        Raises:
            RuntimeError: If tracking is not active
        """
        if not self._is_tracking:
            error_msg = "No active tracking session"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Stop the tracker and get emissions
            emissions = self._tracker.stop()
            end_time = datetime.now()
            
            # Get the final data from the tracker
            final_emissions = self._tracker.final_emissions_data
            
            result = {
                "status": "stopped",
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "end_time": end_time.isoformat(),
                "duration_seconds": final_emissions.duration,
                "emissions_kg": emissions,
                "energy_consumed_kwh": final_emissions.energy_consumed,
                "cpu_energy_kwh": final_emissions.cpu_energy,
                "gpu_energy_kwh": final_emissions.gpu_energy,
                "ram_energy_kwh": final_emissions.ram_energy,
                "country_name": final_emissions.country_name,
                "country_iso_code": final_emissions.country_iso_code,
            }
            
            # Reset state
            self._is_tracking = False
            self._tracker = None
            self._start_time = None
            
            logger.info(f"Stopped tracking: emissions={emissions} kg CO2")
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop tracking: {e}", exc_info=True)
            raise RuntimeError(f"Failed to stop tracking: {e}") from e

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics without stopping the tracking session.
        
        Returns:
            Dict containing current metrics
            
        Raises:
            RuntimeError: If tracking is not active
        """
        if not self._is_tracking:
            error_msg = "No active tracking session"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Get current tracker data
            current_time = datetime.now()
            duration = (current_time - self._start_time).total_seconds() if self._start_time else 0
            
            # Note: CodeCarbon doesn't provide a direct way to get intermediate metrics
            # without stopping, so we provide what we can
            result = {
                "status": "tracking",
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "current_time": current_time.isoformat(),
                "duration_seconds": duration,
                "project_name": self.project_name,
                "note": "Detailed metrics available after stopping tracking",
            }
            
            logger.debug(f"Retrieved current metrics: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get current metrics: {e}") from e

    def is_tracking(self) -> bool:
        """
        Check if tracking is currently active.
        
        Returns:
            True if tracking is active, False otherwise
        """
        return self._is_tracking

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the tracker.
        
        Returns:
            Dict containing tracker status information
        """
        return {
            "is_tracking": self._is_tracking,
            "project_name": self.project_name,
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }
