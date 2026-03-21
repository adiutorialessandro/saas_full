"""
SaaS Full - Strategy Orchestrator
Algoritmi avanzati: MECE Root Cause, McKinsey 7S (OHI), Value Chain, Three Horizons.
"""
from typing import Any, Dict, List, Optional

def run_advanced_diagnostics(kpi_data: Dict[str, Any], 
                             quiz_responses: Dict[str, Any], 
                             benchmarks: Dict[str, Any],
                             business_score_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestra le analisi di livello enterprise basandosi sui dati quantitativi (KPI)
    e qualitativi (Quiz OHI).
    """
    
    # 1. ANALISI MECE (Root Cause Analysis)
    # Identifichiamo il problema primario senza sovrapposizioni
    root_cause = _calculate_mece_root_cause(kpi_data, benchmarks)
    
    # 2. ORGANIZATIONAL HEALTH INDEX (McKinsey 7S)
    ohi = _calculate_ohi_score(quiz_responses)
    
    # 3. VALUE CHAIN & BOTTLENECK
    value_chain = _calculate_value_chain(kpi_data, benchmarks)
    
    # 4. THREE HORIZONS ROADMAP
    # Basato sulla stabilità attuale del business
    horizons = _calculate_three_horizons(business_score_data.get("score", 50))
    
    return {
        "root_cause": root_cause,
        "organizational_health": ohi,
        "value_chain": value_chain,
        "three_horizons": horizons
    }

def _calculate_mece_root_cause(kpi: Dict[str, Any], bench: Dict[str, Any]) -> Dict[str, Any]:
    # Logica a cascata: Cassa -> Margini -> Acquisizione
    runway = kpi.get("runway_mesi", 0) or 0
    margin = kpi.get("margine_pct", 0) or 0
    conv = kpi.get("conversione", 0) or 0
    
    if runway < bench.get("runway", 6):
        return {
            "analysis_path": "Financial > Liquidity > Burn Rate",
            "root_cause": "Crisi di Liquidità Imminente",
            "recommended_action": "Taglio immediato dei costi non core e rinegoziazione dei termini di pagamento."
        }
    elif margin < bench.get("margine", 0.4):
        return {
            "analysis_path": "Financial > Unit Economics > Gross Margin",
            "root_cause": "Incapacità di Estrazione Valore",
            "recommended_action": "Revisione del pricing o dei costi diretti (COGS). Il modello non è profittevole a scala."
        }
    else:
        return {
            "analysis_path": "Growth > Funnel > Conversion Efficiency",
            "root_cause": "Inefficienza Commerciale",
            "recommended_action": "Il prodotto è sano ma il processo di vendita è il collo di bottiglia."
        }

def _calculate_ohi_score(quiz: Dict[str, Any]) -> Dict[str, Any]:
    if not quiz:
        return {"score": 50, "status": "Neutral", "insights": ["Dati qualitativi non disponibili."]}
    
    scores = []
    for v in quiz.values():
        try:
            val = float(v)
            if val <= 1.0:
                scores.append((1.0 - val) * 100)
            else:
                scores.append(val * 20)
        except: pass
    
    avg = (sum(scores) / len(scores)) if scores else 50
    
    status = "Elite" if avg >= 80 else "Stable" if avg >= 60 else "Fragile"
    
    insights = []
    if float(quiz.get('chiarezza_obiettivi', 0)) >= 0.5: insights.append("Mancanza di direzione strategica chiara o condivisa.")
    if float(quiz.get('velocita_decisionale', 0)) >= 0.5: insights.append("Eccessiva burocrazia interna e colli di bottiglia decisionali.")
    if float(quiz.get('fiducia_leadership', 1)) <= 0.5: insights.append("Leadership forte e riconosciuta come punto di riferimento dal team.")
    
    return {
        "score": round(avg),
        "status": status,
        "insights": insights[:3] if insights else ["La cultura aziendale appare allineata e bilanciata."]
    }

def _calculate_value_chain(kpi: Dict[str, Any], bench: Dict[str, Any]) -> Dict[str, Any]:
    # Mappatura delle 5 fasi della catena del valore
    stages = [
        {"stage": "Marketing", "score": 75 if kpi.get('leads_mese', 0) > 10 else 40, "label": "Lead Gen"},
        {"stage": "Sales", "score": int((kpi.get('conversione', 0) / bench.get('conversione', 0.1)) * 100) if bench.get('conversione', 0.1) > 0 else 50, "label": "Conv."},
        {"stage": "Ops", "score": 80 if kpi.get('break_even_ratio', 0) > 1.1 else 45, "label": "Efficiency"},
        {"stage": "Finance", "score": int((kpi.get('margine_pct', 0) / bench.get('margine', 0.5)) * 100) if bench.get('margine', 0.5) > 0 else 50, "label": "Margin"},
        {"stage": "Cash", "score": 90 if kpi.get('runway_mesi', 0) > 12 else 30, "label": "Runway"}
    ]
    
    # Troviamo il bottleneck (punteggio più basso)
    bottleneck = min(stages, key=lambda x: x['score'])
    
    return {
        "value_chain": stages,
        "bottleneck": bottleneck,
        "strategic_insight": f"Il sistema è frenato dalla fase di {bottleneck['stage']}. Focalizzare l'80% delle risorse qui."
    }

def _calculate_three_horizons(score: float) -> Dict[str, Any]:
    urgency = "SURVIVAL" if score < 40 else "MAINTAIN" if score < 70 else "GROWTH"
    
    # Allocazione risorse dinamica
    allocation = {
        "SURVIVAL": {"H1": "90%", "H2": "10%", "H3": "0%"},
        "MAINTAIN": {"H1": "70%", "H2": "20%", "H3": "10%"},
        "GROWTH": {"H1": "50%", "H2": "30%", "H3": "20%"}
    }.get(urgency)

    return {
        "urgency_level": urgency,
        "resource_allocation": allocation,
        "horizons": {
            "Horizon_1_Core": {
                "focus": "Ottimizzazione Cashflow",
                "actions": ["Riduzione churn", "Efficienza operativa"]
            },
            "Horizon_2_Emerging": {
                "focus": "Espansione Mercato",
                "actions": ["Nuovi canali acquisizione", "Upselling"]
            },
            "Horizon_3_Future": {
                "focus": "Innovazione R&D",
                "actions": ["Nuovi prodotti", "Tecnologie disruptive"]
            }
        }
    }