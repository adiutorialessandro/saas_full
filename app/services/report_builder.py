from dataclasses import dataclass
from typing import Any, Dict, List
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

@dataclass
class Inputs:
    settore: str
    modello: str
    mese_riferimento: str
    quiz_risk: List[float]  # 0..1 (1=alto rischio)

def build_report(inp: Inputs) -> Dict[str, Any]:
    avg = sum(inp.quiz_risk) / max(1, len(inp.quiz_risk))
    overall = "VERDE"
    if avg > 0.66:
        overall = "ROSSO"
    elif avg > 0.33:
        overall = "GIALLO"

    per_q = [{"q": i+1, "risk": float(r)} for i, r in enumerate(inp.quiz_risk)]

    return {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento,
                "created_at": utc_now_iso(),
            },
            "state": {"overall": overall, "confidenza": "MEDIA"},
            "quiz": {"avg_risk": float(avg), "per_question": per_q},
            "decisions": {
                "cash": "Rafforzare controllo cassa e pianificare cashflow 13 settimane.",
                "margini": "Verificare struttura costi e proteggere margine lordo.",
                "acq": "Standardizzare funnel e migliorare conversione prima di scalare.",
            },
            "action_plan": [
                "Validare numeri base (incassi/DSO/costi) per aumentare confidenza.",
                "Impostare rituale mensile: cashflow, margine, funnel, pricing.",
                "Standardizzare offerta e follow-up per migliorare conversione.",
            ],
        }
    }
