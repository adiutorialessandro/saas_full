"""
SaaS Full - Business Scoring Engine
Calcola il Business Stability Score (0-100) pesando i KPI fondamentali.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# =========================================================
# UTILITIES DI NORMALIZZAZIONE (Defensive Programming)
# =========================================================
def _to_float(value: Any, default: float = 0.0) -> float:
    """Converte in modo sicuro qualsiasi input in float, gestendo nulli e stringhe sporche."""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            # Pulisce eventuali simboli come '%' o '€'
            value = value.replace('%', '').replace('€', '').replace(',', '.').strip()
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Impossibile convertire '{value}' in float. Uso default: {default}")
        return default

# =========================================================
# FUNZIONI DI SCORING INDIVIDUALI (0–100)
# =========================================================
def runway_score(runway_mesi: Any) -> float:
    r = _to_float(runway_mesi, 0.0)
    if r >= 12: return 100.0
    if r >= 6: return 80.0
    if r >= 3: return 50.0
    return 20.0

def margin_score(margin_pct: Any) -> float:
    m = _to_float(margin_pct, 0.0)
    if m > 1: m /= 100.0  # Normalizza da 40 a 0.40
    
    if m >= 0.60: return 100.0
    if m >= 0.40: return 70.0
    if m >= 0.25: return 40.0
    return 20.0

def conversion_score(conv_rate: Any) -> float:
    c = _to_float(conv_rate, 0.0)
    if c > 1: c /= 100.0
    
    if c >= 0.30: return 100.0
    if c >= 0.10: return 80.0
    if c >= 0.05: return 50.0
    return 20.0

def breakeven_score(be_ratio: Any) -> float:
    b = _to_float(be_ratio, 0.0)
    if b >= 2.0: return 100.0
    if b >= 1.2: return 70.0
    if b >= 1.0: return 50.0
    return 20.0

# =========================================================
# MOTORE PRINCIPALE DI STABILITÀ
# =========================================================
def business_stability_score(kpi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcola il punteggio complessivo 0‑100 del business tramite media pesata.
    Pesi: Runway (35%), Margine (25%), Conversione (20%), Break-even (20%).
    """
    try:
        runway = runway_score(kpi.get("runway_mesi"))
        margin = margin_score(kpi.get("margine_pct"))
        conv = conversion_score(kpi.get("conversione"))
        breakeven = breakeven_score(kpi.get("break_even_ratio"))

        # Media pesata
        score_raw = (runway * 0.35) + (margin * 0.25) + (conv * 0.20) + (breakeven * 0.20)
        score = round(score_raw)

        # Determinazione dello Status
        if score >= 75:
            status, tone, icon = "Strong", "positive", "🟢"
        elif score >= 50:
            status, tone, icon = "Attention", "warning", "🟡"
        elif score >= 30:
            status, tone, icon = "Risk", "warning", "🟠"
        else:
            status, tone, icon = "Critical", "danger", "🔴"

        return {
            "score": score,
            "status": status,
            "tone": tone,
            "icon": icon,
            "components": {
                "runway": runway,
                "margin": margin,
                "conversion": conv,
                "breakeven": breakeven,
            },
        }
    except Exception as e:
        logger.error(f"Errore nel calcolo del Business Stability Score: {str(e)}", exc_info=True)
        return {"score": 50, "status": "Attention", "tone": "warning", "icon": "🟡", "components": {}}

def executive_insight(vm: Dict[str, Any]) -> str:
    """Genera l'insight testuale dinamico per l'Executive Summary."""
    kpi = vm.get("kpi") or {}
    score_data = business_stability_score(kpi)
    score = score_data["score"]

    runway = _to_float(kpi.get("runway_mesi"))
    margin = _to_float(kpi.get("margine_pct"))
    conv = _to_float(kpi.get("conversione"))

    notes = []
    if runway < 4:
        notes.append("La runway è limitata e richiede interventi immediati sulla liquidità.")
    if margin > 0 and (margin < 0.30 or margin < 30):
        notes.append("La marginalità operativa è troppo debole per finanziare la crescita.")
    if conv > 0 and (conv < 0.05 or conv < 5):
        notes.append("Il motore commerciale (conversione) disperde troppe opportunità.")

    if score >= 75:
        opening = "L'architettura aziendale risulta solida e scalabile."
    elif score >= 50:
        opening = "Il modello di business è operativo ma presenta fragilità sistemiche."
    else:
        opening = "Allerta massima: l'azienda mostra criticità che minacciano la continuità."

    middle = " " + " ".join(notes[:2]) if notes else ""
    return f"{opening}{middle} Business Stability Score: {score}/100."

def report_header_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    """Prepara l'header primario per il report PDF."""
    return {
        "business_stability": business_stability_score(vm.get("kpi") or {}),
        "executive_insight": executive_insight(vm),
    }