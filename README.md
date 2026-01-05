
# MCP-CodeCarbon

Serveur **MCP** qui permets de mesurer la consommation énergétique et les émissions carbone d’un programme Python à l’aide de la bibliothèque **CodeCarbon**.

Ce projet a été réalisé dans un cadre académique afin de découvrir :

- le protocole MCP,
- l’intégration d’outils côté serveur,
- la mesure d’impact énergétique des calculs logiciels.

---

## Fonctionnalités

Le serveur expose plusieurs outils MCP :

- `start_tracking` : démarre le suivi énergétique
- `stop_tracking` : arrête le suivi et retourne les métriques finales
- `get_status` : indique si un suivi est en cours
- `get_current_metrics` : retourne des informations temporelles sur le suivi en cours

Les mesures sont réalisées via CodeCarbon (CPU, RAM, GPU si disponible).

---

## Prérequis

- Python =>**3.10**
- Accès aux performances matérielles mais certaines mesures peuvent être estimées selon la machine

---

## Installation

### Avec `pip` 

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
