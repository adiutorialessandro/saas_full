from __future__ import annotations

from typing import Any, Dict, Optional


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _trend_direction(delta: Any, inverse: bool = False) -> str:
    d = _to_float(delta, 0.0)
    if d is None:
        return "stable"

    if inverse:
        d = -d

    if d > 0:
        return "up"
    if d < 0:
        return "down"
    return "stable"


def health_status(overall_score: Any) -> Dict[str, str]:
    score = _to_float(overall_score, 50.0)
    if score is None:
        score = 50.0

    if score >= 70:
        return {
            "label": "Healthy",
            "tone": "positive",
            "description": "La stabilità complessiva appare solida e sufficientemente difesa.",
        }

    if score >= 45:
        return {
            "label": "Watchlist",
            "tone": "warning",
            "description": "Il business è operativo ma richiede attenzione attiva su priorità e ritmo esecutivo.",
        }

    return {
        "label": "Critical",
        "tone": "danger",
        "description": "La struttura richiede interventi ravvicinati per evitare deterioramento della stabilità.",
    }


def dominant_priority(risks: Dict[str, Any]) -> Dict[str, str]:
    cash = _to_float((risks or {}).get("cash"), 50.0)
    margini = _to_float((risks or {}).get("margini"), 50.0)
    acq = _to_float((risks or {}).get("acq"), 50.0)

    items = [
        (
            "cash",
            cash,
            "Proteggere la cassa",
            "La priorità è aumentare visibilità su liquidità, incassi attesi e tenuta di breve periodo.",
        ),
        (
            "margini",
            margini,
            "Difendere i margini",
            "La priorità è migliorare qualità economica, pricing e disciplina sulla redditività.",
        ),
        (
            "acq",
            acq,
            "Stabilizzare l’acquisizione",
            "La priorità è rendere il motore commerciale più prevedibile, leggibile e ripetibile.",
        ),
    ]

    key, value, title, description = max(items, key=lambda x: x[1] if x[1] is not None else 50.0)

    return {
        "key": key,
        "title": title,
        "description": description,
        "value": f"{round(value or 50.0, 1)}%",
    }


def trend_badge(delta: Any, inverse: bool = False) -> Dict[str, str]:
    d = _to_float(delta, 0.0)
    if d is None:
        d = 0.0

    direction = _trend_direction(d, inverse=inverse)
    shown = -d if inverse else d

    if direction == "up":
        return {
            "direction": "up",
            "tone": "positive",
            "icon": "↑",
            "value": f"+{abs(round(shown, 1))}",
            "label": "in miglioramento",
        }

    if direction == "down":
        return {
            "direction": "down",
            "tone": "danger",
            "icon": "↓",
            "value": f"-{abs(round(shown, 1))}",
            "label": "in peggioramento",
        }

    return {
        "direction": "stable",
        "tone": "neutral",
        "icon": "→",
        "value": "0.0",
        "label": "stabile",
    }


def comparative_insight(vm: Dict[str, Any], delta: Dict[str, Any]) -> str:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}

    score_delta = _to_float((delta or {}).get("score"), 0.0)
    cash_delta = _to_float((delta or {}).get("cash"), 0.0)
    marg_delta = _to_float((delta or {}).get("margini"), 0.0)
    acq_delta = _to_float((delta or {}).get("acq"), 0.0)

    overall_score = _to_float(state.get("overall_score"), 50.0)
    priority = dominant_priority(risks)

    if score_delta is None or abs(score_delta) < 0.1:
        opening = "Rispetto allo scan precedente, la stabilità complessiva appare sostanzialmente invariata."
    elif score_delta > 0:
        opening = f"Rispetto allo scan precedente, la stabilità complessiva migliora di {round(score_delta, 1)} punti."
    else:
        opening = f"Rispetto allo scan precedente, la stabilità complessiva peggiora di {abs(round(score_delta, 1))} punti."

    area_comments = []

    if cash_delta is not None and abs(cash_delta) >= 0.1:
        area_comments.append("Il rischio cassa si riduce" if cash_delta < 0 else "il rischio cassa cresce")

    if marg_delta is not None and abs(marg_delta) >= 0.1:
        area_comments.append("i margini migliorano" if marg_delta < 0 else "la qualità economica si indebolisce")

    if acq_delta is not None and abs(acq_delta) >= 0.1:
        area_comments.append("l’acquisizione migliora" if acq_delta < 0 else "l’acquisizione resta sotto pressione")

    middle = ""
    if area_comments:
        middle = " " + ", ".join(area_comments) + "."

    if overall_score >= 70:
        closing = " La priorità ora è consolidare il vantaggio emerso e renderlo replicabile."
    elif overall_score >= 45:
        closing = f" La priorità manageriale attuale è: {priority['title'].lower()}."
    else:
        closing = f" La priorità immediata è: {priority['title'].lower()}, prima di aumentare complessità o crescita commerciale."

    return opening + middle + closing


def report_header_payload(vm: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}

    score = _to_float(state.get("overall_score"), 50.0)

    return {
        "health": health_status(score),
        "priority": dominant_priority(risks),
        "score_trend": trend_badge((delta or {}).get("score"), inverse=False),
        "cash_trend": trend_badge((delta or {}).get("cash"), inverse=True),
        "margini_trend": trend_badge((delta or {}).get("margini"), inverse=True),
        "acq_trend": trend_badge((delta or {}).get("acq"), inverse=True),
        "comparative_insight": comparative_insight(vm, delta or {}),
    }