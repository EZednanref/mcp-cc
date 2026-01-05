"""
MCP Server for CodeCarbon energy tracking.

This module implements the Model Context Protocol server that exposes
CodeCarbon tracking capabilities as tools for AI agents.
"""

import logging
import asyncio
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .tracker import CodeCarbonTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global tracker instance
tracker = CodeCarbonTracker()

# Create MCP server
app = Server("mcp-codecarbon")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available CodeCarbon tools.
    
    Returns:
        List of available tools for energy tracking
    """
    return [
        Tool(
            name="start_tracking",
            description=(
                "Start energy and carbon tracking. This begins monitoring CPU/GPU energy "
                "consumption and calculating carbon emissions. Call this before running "
                "code you want to measure."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "measure_power_secs": {
                        "type": "integer",
                        "description": "Interval in seconds for power measurement (default: 15)",
                        "default": 15,
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="stop_tracking",
            description=(
                "Stop energy tracking and return comprehensive metrics including total "
                "energy consumed (kWh), CPU energy, GPU energy, RAM energy, and carbon "
                "emissions (kg CO2). Call this after your code has finished executing."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_status",
            description=(
                "Get the current status of the energy tracker, including whether tracking "
                "is active and when it was started. Does not stop or interfere with tracking."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_current_metrics",
            description=(
                "Get current tracking metrics without stopping the session. Note: detailed "
                "energy metrics are only available after stopping tracking. Use this to check "
                "tracking duration and status."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """
    Handle tool calls for CodeCarbon operations.
    
    Args:
        name: Name of the tool to call
        arguments: Arguments for the tool
        
    Returns:
        Sequence of TextContent with tool results
        
    Raises:
        ValueError: If tool name is unknown
    """
    try:
        if name == "start_tracking":
            # Extract optional parameters
            measure_power_secs = arguments.get("measure_power_secs", 15)
            
            result = tracker.start_tracking(measure_power_secs=measure_power_secs)
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ Energy tracking started successfully\n\n"
                         f"Project: {result['project_name']}\n"
                         f"Start time: {result['start_time']}\n"
                         f"Measurement interval: {measure_power_secs}s\n\n"
                         f"Tracking CPU/GPU energy consumption and carbon emissions.",
                )
            ]
        
        elif name == "stop_tracking":
            result = tracker.stop_tracking()
            
            return [
                TextContent(
                    type="text",
                    text=f"🛑 Energy tracking stopped\n\n"
                         f"📊 Tracking Summary:\n"
                         f"  Duration: {result['duration_seconds']:.2f} seconds\n"
                         f"  Start: {result['start_time']}\n"
                         f"  End: {result['end_time']}\n\n"
                         f"⚡ Energy Consumption:\n"
                         f"  Total: {result['energy_consumed_kwh']:.6f} kWh\n"
                         f"  CPU: {result['cpu_energy_kwh']:.6f} kWh\n"
                         f"  GPU: {result['gpu_energy_kwh']:.6f} kWh\n"
                         f"  RAM: {result['ram_energy_kwh']:.6f} kWh\n\n"
                         f"🌍 Carbon Emissions:\n"
                         f"  Total: {result['emissions_kg']:.6f} kg CO2eq\n"
                         f"  Location: {result['country_name']} ({result['country_iso_code']})",
                )
            ]
        
        elif name == "get_status":
            result = tracker.get_status()
            
            status_text = "✅ Tracking active" if result['is_tracking'] else "⏸️ Not tracking"
            start_info = f"\nStart time: {result['start_time']}" if result['start_time'] else ""
            
            return [
                TextContent(
                    type="text",
                    text=f"{status_text}\n\n"
                         f"Project: {result['project_name']}{start_info}",
                )
            ]
        
        elif name == "get_current_metrics":
            result = tracker.get_current_metrics()
            
            return [
                TextContent(
                    type="text",
                    text=f"📊 Current Tracking Metrics\n\n"
                         f"Status: {result['status']}\n"
                         f"Project: {result['project_name']}\n"
                         f"Start time: {result['start_time']}\n"
                         f"Current time: {result['current_time']}\n"
                         f"Duration: {result['duration_seconds']:.2f} seconds\n\n"
                         f"ℹ️ {result['note']}",
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"❌ Error: {str(e)}",
            )
        ]


async def run_server() -> None:
    """Run the MCP server using stdio transport."""
    logger.info("Starting MCP-CodeCarbon server")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
