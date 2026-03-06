from typing import Dict, Any, List

def strategic_actions(kpi: Dict[str, Any]) -> List[str]:

    actions = []

    runway = kpi.get("runway_mesi")
    conversion = kpi.get("conversione")
    be = kpi.get("break_even_ratio")

    if runway and runway < 4:
        actions.append("Ridurre burn 10-20% per estendere runway.")

    if conversion and conversion < 0.10:
        actions.append("Migliorare funnel commerciale e follow-up.")

    if be and be < 1.1:
        actions.append("Revisione pricing e controllo costi variabili.")

    if not actions:
        actions.append("Situazione stabile: monitorare KPI settimanali.")

    return actions
