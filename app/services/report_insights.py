from __future__ import annotations

from typing import Any, Dict, Optional


STATUS_LABELS = {
    "positive": "Healthy",
    "warning": "Watchlist",
    "danger": "Critical",
}

PRIORITY_META = {
    "cash": {
        "title": "Proteggere la cassa",
        "description": "La priorità è aumentare visibilità su liquidità, incassi attesi e tenuta di breve periodo.",
        "focus": "stabilità finanziaria di breve periodo",
        "strength_if_low": "buona tenuta finanziaria",
    },
    "margini": {
        "title": "Difendere i margini",
        "description": "La priorità è migliorare qualità economica, pricing e disciplina sulla redditività.",
        "focus": "qualità economica e disciplina del margine",
        "strength_if_low": "qualità economica relativamente difesa",
    },
    "acq": {
        "title": "Stabilizzare l’acquisizione",
        "description": "La priorità è rendere il motore commerciale più prevedibile, leggibile e ripetibile.",
        "focus": "continuità e prevedibilità commerciale",
        "strength_if_low": "buona continuità del motore commerciale",
    },
}

AREA_LABELS = {
    "cash": "la cassa",
    "margini": "i margini",
    "acq": "l’acquisizione",
}


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _risk_value(raw: Any) -> float:
    """
    Restituisce il rischio in percentuale 0..100.
    Accetta sia valori 0..1 che 0..100.
    """
    value = _to_float(raw, 50.0)
    if value is None:
        return 50.0
    if value <= 1.0:
        value *= 100.0
    return max(0.0, min(100.0, value))


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
            "label": STATUS_LABELS["positive"],
            "tone": "positive",
            "description": "La stabilità complessiva appare solida e sufficientemente difesa.",
            "icon": "🟢",
            "summary": "Stabilità complessiva solida.",
        }

    if score >= 45:
        return {
            "label": STATUS_LABELS["warning"],
            "tone": "warning",
            "description": "Il business è operativo ma richiede attenzione attiva su priorità e ritmo esecutivo.",
            "icon": "🟡",
            "summary": "Stabilità moderata con attenzione attiva.",
        }

    return {
        "label": STATUS_LABELS["danger"],
        "tone": "danger",
        "description": "La struttura richiede interventi ravvicinati per evitare deterioramento della stabilità.",
        "icon": "🔴",
        "summary": "Stabilità critica da presidiare subito.",
    }


def dominant_priority(risks: Dict[str, Any]) -> Dict[str, str]:
    values = {
        "cash": _risk_value((risks or {}).get("cash")),
        "margini": _risk_value((risks or {}).get("margini")),
        "acq": _risk_value((risks or {}).get("acq")),
    }

    key = max(values, key=lambda item: values[item])
    meta = PRIORITY_META[key]

    return {
        "key": key,
        "title": meta["title"],
        "description": meta["description"],
        "focus": meta["focus"],
        "value": f"{round(values[key], 1)}%",
    }


def strongest_area(risks: Dict[str, Any]) -> Dict[str, str]:
    values = {
        "cash": _risk_value((risks or {}).get("cash")),
        "margini": _risk_value((risks or {}).get("margini")),
        "acq": _risk_value((risks or {}).get("acq")),
    }

    key = min(values, key=lambda item: values[item])
    meta = PRIORITY_META[key]

    return {
        "key": key,
        "title": meta["strength_if_low"],
        "description": f"L’area più difesa oggi riguarda {meta['focus']}.",
        "area_label": AREA_LABELS.get(key, "questa area"),
        "value": f"{round(values[key], 1)}%",
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


def strategic_diagnosis(vm: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, str]:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}

    health = health_status(state.get("overall_score"))
    priority = dominant_priority(risks)
    strength = strongest_area(risks)
    score_trend = trend_badge((delta or {}).get("score"), inverse=False)

    if score_trend["direction"] == "up":
        trend_sentence = (
            f"Rispetto allo scan precedente emerge un miglioramento della stabilità complessiva ({score_trend['icon']} {score_trend['value']})."
        )
    elif score_trend["direction"] == "down":
        trend_sentence = (
            f"Rispetto allo scan precedente emerge un peggioramento della stabilità complessiva ({score_trend['icon']} {score_trend['value']})."
        )
    else:
        trend_sentence = "Rispetto allo scan precedente il quadro appare sostanzialmente stabile."

    headline = f"{health['icon']} {health['label']}"
    diagnosis = (
        f"La tua azienda si trova oggi in una fase di {health['label'].lower()}. "
        f"Il principale punto di attenzione riguarda {priority['focus']}. "
        f"Il punto relativamente più difeso oggi riguarda invece {strength['area_label']}."
    )

    priorities = (
        f"Priorità attuale: {priority['title']}. "
        f"{priority['description']}"
    )

    return {
        "headline": headline,
        "status_label": health["label"],
        "status_tone": health["tone"],
        "summary": health["description"],
        "diagnosis": diagnosis,
        "trend": trend_sentence,
        "priority": priorities,
        "strength": strength["description"],
        "strength_label": strength["title"],
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

    if overall_score is not None and overall_score >= 70:
        closing = " La priorità ora è consolidare il vantaggio emerso e renderlo replicabile."
    elif overall_score is not None and overall_score >= 45:
        closing = f" La priorità manageriale attuale è: {priority['title'].lower()}."
    else:
        closing = f" La priorità immediata è: {priority['title'].lower()}, prima di aumentare complessità o crescita commerciale."

    return opening + middle + closing


def executive_insight(vm: Dict[str, Any]) -> str:
    """
    Genera un insight manageriale sintetico a partire dai dati del report.
    Lavora con:
    - triad_index oppure state.overall_score
    - risks.cash / risks.margini / risks.acq
    - kpi.runway_mesi / break_even_ratio / margine_pct / conversione / burn_cash_ratio
    """

    state = vm.get("state") or {}
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    triad = vm.get("triad_index")
    if triad is None:
        triad = state.get("overall_score")

    try:
        triad = float(triad) if triad is not None else None
    except Exception:
        triad = None

    def _risk_pct(value: Any, default: float = 50.0) -> float:
        try:
            if value is None:
                return default
            v = float(value)
            if v <= 1:
                v *= 100.0
            return max(0.0, min(100.0, v))
        except Exception:
            return default

    cash = _risk_pct(risks.get("cash"))
    margini = _risk_pct(risks.get("margini"))
    acq = _risk_pct(risks.get("acq"))

    dominant_key = max(
        [("cash", cash), ("margini", margini), ("acq", acq)],
        key=lambda x: x[1],
    )[0]

    if dominant_key == "cash":
        dominant_area = "tenuta finanziaria"
        dominant_explanation = (
            "la crescita è oggi frenata soprattutto dalla visibilità di cassa e dalla sostenibilità del breve periodo"
        )
    elif dominant_key == "margini":
        dominant_area = "qualità economica"
        dominant_explanation = (
            "la crescita è oggi frenata soprattutto dalla protezione del margine e dalla qualità economica del modello"
        )
    else:
        dominant_area = "motore commerciale"
        dominant_explanation = (
            "la crescita è oggi frenata soprattutto dalla prevedibilità dell’acquisizione e dalla continuità del funnel"
        )

    runway = kpi.get("runway_mesi")
    break_even = kpi.get("break_even_ratio")
    margine_pct = kpi.get("margine_pct")
    conversione = kpi.get("conversione")
    burn_cash_ratio = kpi.get("burn_cash_ratio")

    runway_note = None
    try:
        if runway is not None:
            runway = float(runway)
            if runway < 2:
                runway_note = "La runway disponibile è molto corta e richiede interventi immediati."
            elif runway < 4:
                runway_note = "La runway disponibile è limitata e richiede controllo stretto del cashflow."
    except Exception:
        pass

    break_even_note = None
    try:
        if break_even is not None:
            break_even = float(break_even)
            if break_even < 1:
                break_even_note = "I ricavi non coprono ancora pienamente il punto di pareggio."
    except Exception:
        pass

    margin_note = None
    try:
        if margine_pct is not None:
            m = float(margine_pct)
            if m > 1:
                m /= 100.0
            if m < 0.30:
                margin_note = "Il margine lordo è troppo basso per sostenere crescita sana."
            elif m < 0.40:
                margin_note = "Il margine lordo va difeso meglio per evitare erosione."
    except Exception:
        pass

    conversion_note = None
    try:
        if conversione is not None:
            c = float(conversione)
            if c > 1:
                c /= 100.0
            if c < 0.05:
                conversion_note = "La conversione commerciale è debole e limita la trasformazione dei lead."
            elif c < 0.10:
                conversion_note = "La conversione commerciale è migliorabile e va resa più stabile."
    except Exception:
        pass

    burn_note = None
    try:
        if burn_cash_ratio is not None:
            b = float(burn_cash_ratio)
            if b > 1:
                b /= 100.0
            if b > 0.25:
                burn_note = "Il burn assorbe una quota troppo alta della cassa disponibile."
    except Exception:
        pass

    if triad is None:
        opening = "Dati insufficienti per formulare una lettura strategica affidabile."
    elif triad >= 75:
        opening = (
            "L’azienda mostra una struttura complessivamente solida, con condizioni favorevoli per consolidare e scalare."
        )
    elif triad >= 50:
        opening = (
            "L’azienda ha basi operative presenti, ma la crescita è ancora frenata da alcune fragilità chiave."
        )
    else:
        opening = (
            "L’azienda mostra segnali di fragilità strutturale e richiede priorità nette prima di aumentare la spinta alla crescita."
        )

    detail_notes = [
        note
        for note in [runway_note, break_even_note, margin_note, conversion_note, burn_note]
        if note
    ]

    middle = ""
    if detail_notes:
        middle = " " + " ".join(detail_notes[:2])

    if triad is None:
        closing = " È consigliabile completare i KPI principali per ottenere un’indicazione più affidabile."
    elif triad >= 75:
        closing = (
            f" In sintesi, il sistema è sano ma la priorità manageriale resta {dominant_area}: serve consolidare ciò che funziona e aumentare la replicabilità."
        )
    elif triad >= 50:
        closing = (
            f" In sintesi, {dominant_explanation}. La priorità è correggere questo vincolo prima di accelerare ulteriormente."
        )
    else:
        closing = (
            f" In sintesi, {dominant_explanation}. La priorità immediata non è crescere di più, ma ripristinare controllo, protezione economica e continuità esecutiva."
        )

    return opening + middle + closing


def runway_explanation() -> str:
    return (
        "Il cash runway indica per quanti mesi l'azienda può continuare a operare "
        "con la cassa disponibile mantenendo l'attuale ritmo di spesa."
    )


def report_header_payload(vm: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}

    score = _to_float(state.get("overall_score"), 50.0)

    return {
        "health": health_status(score),
        "priority": dominant_priority(risks),
        "strength": strongest_area(risks),
        "score_trend": trend_badge((delta or {}).get("score"), inverse=False),
        "cash_trend": trend_badge((delta or {}).get("cash"), inverse=True),
        "margini_trend": trend_badge((delta or {}).get("margini"), inverse=True),
        "acq_trend": trend_badge((delta or {}).get("acq"), inverse=True),
        "comparative_insight": comparative_insight(vm, delta or {}),
        "diagnosis": strategic_diagnosis(vm, delta or {}),
        "executive_insight": executive_insight(vm),
        "runway_explanation": runway_explanation(),
    }