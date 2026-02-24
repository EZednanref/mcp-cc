"""Test direct du tracker CodeCarbon (sans passer par MCP)."""

import time
from mcp_codecarbon.tracker import CodeCarbonTracker

tracker = CodeCarbonTracker()

# 1. Status initial
print("=== Status initial ===")
print(tracker.status())

# 2. Start/stop manuel
print("\n=== Start/Stop manuel ===")
tracker.start(measure_power_secs=1)
print(tracker.status())
time.sleep(2)
print(tracker.stop())

# 3. run_and_measure — mesure l'exécution d'une commande
print("\n=== run_and_measure ===")
result = tracker.run_and_measure("python3 -c 'sum(range(10_000_000))'", measure_power_secs=1)
for k, v in result.items():
    print(f"  {k}: {v}")
