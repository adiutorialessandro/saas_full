"""
Three Horizons of Growth Framework
Pianificatore strategico per l'allocazione delle risorse nel tempo.
"""
from typing import Dict, Any

def three_horizons_action_plan(kpi: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera una roadmap dinamica basata sullo stato di salute aziendale (Business Stability Score).
    """
    runway = kpi.get("runway_mesi")
    conversione = kpi.get("conversione")
    break_even = kpi.get("break_even_ratio")
    
    score = score_data.get("score", 50)
    
    # Regola di business: Allocazione Dinamica
    if score < 50 or (runway and runway < 4):
        allocation = {"H1": "90%", "H2": "10%", "H3": "0% (Sospeso)"}
        urgency = "CRITICAL"
    elif score < 75:
        allocation = {"H1": "75%", "H2": "20%", "H3": "5%"}
        urgency = "MODERATE"
    else:
        allocation = {"H1": "60%", "H2": "25%", "H3": "15%"}
        urgency = "STABLE"

    # Composizione Azioni Orizzonte 1 (Breve Termine / Core)
    h1_actions = []
    if runway and runway < 4:
        h1_actions.append("Eseguire cost-cutting immediato sui costi fissi per estendere la runway.")
    if break_even and break_even < 1.1:
        h1_actions.append("Discontinuare i clienti o i servizi a marginalità negativa.")
    if not h1_actions:
        h1_actions.append("Ottimizzare i processi core per massimizzare il Free Cash Flow.")

    # Composizione Azioni Orizzonte 2 (Medio Termine / Scalabilità)
    h2_actions = []
    if conversione and conversione < 0.10:
        h2_actions.append("Sviluppare un nuovo canale di traffico qualificato per migliorare le conversioni.")
    else:
        h2_actions.append("Strutturare protocolli di up-selling sistematico sui clienti alto-spendenti.")

    # Composizione Azioni Orizzonte 3 (Lungo Termine / Innovazione)
    h3_actions = []
    if urgency == "CRITICAL":
        h3_actions.append("Sospendere gli investimenti in R&D ad alto rischio fino al consolidamento della cassa.")
    else:
        h3_actions.append("Analizzare opportunità di integrazione AI per creare un vantaggio sleale sul prodotto.")
        h3_actions.append("Mappare l'ingresso strategico in un mercato estero o in un settore adiacente.")

    return {
        "resource_allocation": allocation,
        "urgency_level": urgency,
        "horizons": {
            "Horizon_1_Core": {
                "timeframe": "0-6 Mesi",
                "focus": "Sopravvivenza e Generazione Cassa",
                "actions": h1_actions
            },
            "Horizon_2_Emerging": {
                "timeframe": "6-18 Mesi",
                "focus": "Automazione e Scalabilità",
                "actions": h2_actions
            },
            "Horizon_3_Future": {
                "timeframe": "18-36 Mesi",
                "focus": "Innovazione e Diversificazione",
                "actions": h3_actions
            }
        }
    }