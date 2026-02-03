# Local MCP v0 (Fritsch)

FR

Serveur MCP local qui encapsule `EmissionsTracker` de CodeCarbon et expose les outils :

- start_measurement
- stop_measurement
- get_last_run
- list_recent_runs

## Lancer

Installer les dépendances :

```bash
pip install codecarbon mcp
```

Démarrer le serveur (transport stdio) :

```bash
python experiments/local_mcp_v0_fritsch/mcp_server.py
```

## Notes

- Les mesures sont enregistrées dans le même `emissions.csv` que le tracker CodeCarbon standard.
- `get_last_run` et `list_recent_runs` lisent ce fichier CSV.

---

EN

Local MCP server that wraps CodeCarbon's `EmissionsTracker` and exposes tools:

- start_measurement
- stop_measurement
- get_last_run
- list_recent_runs

## Run

Install deps in your environment:

```bash
pip install codecarbon mcp
```

Start the server (stdio transport):

```bash
python experiments/local_mcp_v0_fritsch/mcp_server.py
```

## Notes

- Measurements are saved to the same `emissions.csv` as the standard CodeCarbon tracker.
- `get_last_run` and `list_recent_runs` read from that CSV file.
