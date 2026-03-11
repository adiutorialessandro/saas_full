from __future__ import annotations

from typing import Any, Dict, Optional


# =========================================================
# KPI NORMALIZATION UTILITIES
# =========================================================


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


# =========================================================
# KPI SCORING FUNCTIONS (0–100)
# =========================================================


def runway_score(runway: Any) -> float:
    r = _to_float(runway, 0.0)

    if r is None:
        return 50

    if r >= 12:
        return 100

    if r >= 6:
        return 80

    if r >= 3:
        return 50

    return 20


def margin_score(margin: Any) -> float:
    m = _to_float(margin, 0.0)

    if m is None:
        return 50

    # support values like 44 or 0.44
    if m > 1:
        m = m / 100

    if m >= 0.60:
        return 100

    if m >= 0.40:
        return 70

    if m >= 0.25:
        return 40

    return 20


def conversion_score(conv: Any) -> float:
    c = _to_float(conv, 0.0)

    if c is None:
        return 50

    if c > 1:
        c = c / 100

    if c >= 0.30:
        return 100

    if c >= 0.10:
        return 80

    if c >= 0.05:
        return 50

    return 20


def breakeven_score(value: Any) -> float:
    r = _to_float(value, 0.0)

    if r is None:
        return 50

    if r >= 2:
        return 100

    if r >= 1.2:
        return 70

    if r >= 1:
        return 50

    return 20


# =========================================================
# BUSINESS STABILITY SCORE
# =========================================================


def business_stability_score(kpi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcola il punteggio complessivo 0‑100 del business.

    Pesi:
    Runway        35%
    Margine       25%
    Conversione   20%
    Break-even    20%
    """

    runway = runway_score(kpi.get("runway_mesi"))
    margin = margin_score(kpi.get("margine_pct"))
    conv = conversion_score(kpi.get("conversione"))
    breakeven = breakeven_score(kpi.get("break_even_ratio"))

    score = (
        runway * 0.35
        + margin * 0.25
        + conv * 0.20
        + breakeven * 0.20
    )

    score = round(score)

    if score >= 75:
        status = "Strong"
        tone = "positive"
        icon = "🟢"

    elif score >= 50:
        status = "Attention"
        tone = "warning"
        icon = "🟡"

    elif score >= 30:
        status = "Risk"
        tone = "warning"
        icon = "🟠"

    else:
        status = "Critical"
        tone = "danger"
        icon = "🔴"

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


# =========================================================
# STRATEGIC INSIGHT GENERATION
# =========================================================


def executive_insight(vm: Dict[str, Any]) -> str:
    state = vm.get("state") or {}
    kpi = vm.get("kpi") or {}

    score_data = business_stability_score(kpi)
    score = score_data["score"]

    runway = _to_float(kpi.get("runway_mesi"))
    margin = _to_float(kpi.get("margine_pct"))
    conv = _to_float(kpi.get("conversione"))

    notes = []

    if runway is not None and runway < 4:
        notes.append("La runway è limitata e richiede attenzione sulla cassa.")

    if margin is not None:
        m = margin
        if m > 1:
            m = m / 100

        if m < 0.30:
            notes.append("Il margine lordo è troppo basso per sostenere crescita sana.")

    if conv is not None:
        c = conv
        if c > 1:
            c = c / 100

        if c < 0.05:
            notes.append("La conversione commerciale è debole.")

    if score >= 75:
        opening = "L'azienda mostra una struttura complessivamente solida."
    elif score >= 50:
        opening = "L'azienda è operativa ma presenta alcune fragilità strutturali."
    else:
        opening = "L'azienda mostra segnali di fragilità che richiedono interventi prioritari."

    middle = ""

    if notes:
        middle = " " + " ".join(notes[:2])

    closing = f" Business Stability Score: {score}/100."

    return opening + middle + closing


# =========================================================
# REPORT HEADER PAYLOAD
# =========================================================


def report_header_payload(vm: Dict[str, Any]) -> Dict[str, Any]:

    kpi = vm.get("kpi") or {}

    score_data = business_stability_score(kpi)

    return {
        "business_stability": score_data,
        "executive_insight": executive_insight(vm),
    }