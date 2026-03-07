
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
    quiz = [float(x) for x in (inp.quiz_risk or [])]
    if not quiz:
        quiz = [0.5] * 10

    avg = sum(quiz) / len(quiz)

    if avg >= 0.66:
        overall = "ROSSO"
    elif avg >= 0.33:
        overall = "GIALLO"
    else:
        overall = "VERDE"

    overall_score = round(avg * 100.0, 2)
    confidence = 55

    def clamp01(v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    def label_from_risk(r: float) -> str:
        if r >= 0.66:
            return "ROSSO"
        if r >= 0.33:
            return "GIALLO"
        return "VERDE"

    def avg_slice(values: List[float], start: int, end: int) -> float:
        chunk = values[start:end]
        if not chunk:
            return 0.5
        return sum(chunk) / len(chunk)

    risk_cash = clamp01(avg_slice(quiz, 0, 4))
    risk_margini = clamp01(avg_slice(quiz, 2, 7))
    risk_acq = clamp01(avg_slice(quiz, 4, 10))

    dominant_area = max(
        [
            ("Finanziario", risk_cash),
            ("Margini", risk_margini),
            ("Commerciale", risk_acq),
        ],
        key=lambda x: x[1],
    )[0]

    if dominant_area == "Finanziario":
        risk_profile = "Profilo di rischio: Finanziario"
    elif dominant_area == "Margini":
        risk_profile = "Profilo di rischio: Economico-Marginale"
    else:
        risk_profile = "Profilo di rischio: Operativo-Commerciale"

    maturity_score = round((1.0 - avg) * 100.0, 2)

    if maturity_score >= 70:
        maturity_label = "Maturità: Avanzata"
    elif maturity_score >= 45:
        maturity_label = "Maturità: Intermedia"
    else:
        maturity_label = "Maturità: Fragile"

    per_q = [{"q": i + 1, "risk": float(r)} for i, r in enumerate(quiz)]

    def indicator(title: str, desc: str, risk: float) -> Dict[str, Any]:
        risk = clamp01(risk)
        return {
            "title": title,
            "desc": desc,
            "score01": round(risk, 4),
            "label": label_from_risk(risk),
            "value_str": f"{round(risk * 100)} / 100",
        }

    indicators = [
        indicator(
            "Tenuta finanziaria",
            "Misura quanto la struttura di cassa e la capacità di coprire il breve periodo risultano solide.",
            risk_cash,
        ),
        indicator(
            "Qualità dei margini",
            "Valuta la protezione del margine e la sostenibilità economica della struttura attuale.",
            risk_margini,
        ),
        indicator(
            "Capacità di acquisizione",
            "Indica quanto il motore commerciale appare prevedibile, ripetibile e scalabile.",
            risk_acq,
        ),
        indicator(
            "Controllo manageriale",
            "Sintetizza qualità delle decisioni, lettura KPI ed esecuzione operativa.",
            clamp01(avg_slice(quiz, 7, 10)),
        ),
    ]

    alerts: List[Dict[str, str]] = []
    if risk_cash >= 0.66:
        alerts.append({
            "level": "ROSSO",
            "text": "La tenuta finanziaria appare fragile: servono maggiore visibilità sul breve periodo e un controllo più stretto della cassa.",
        })
    elif risk_cash >= 0.33:
        alerts.append({
            "level": "GIALLO",
            "text": "La situazione di cassa richiede monitoraggio più frequente per evitare tensioni e ridurre l’incertezza operativa.",
        })

    if risk_margini >= 0.66:
        alerts.append({
            "level": "ROSSO",
            "text": "Margini e struttura costi non risultano sufficientemente protetti: c’è rischio di erosione economica e di crescita poco sostenibile.",
        })
    elif risk_margini >= 0.33:
        alerts.append({
            "level": "GIALLO",
            "text": "La qualità dei margini va rafforzata: servono più disciplina su pricing, costi e priorità commerciali.",
        })

    if risk_acq >= 0.66:
        alerts.append({
            "level": "ROSSO",
            "text": "Il motore di acquisizione non appare ancora stabile o ripetibile: il business rischia forte dipendenza da iniziative episodiche.",
        })
    elif risk_acq >= 0.33:
        alerts.append({
            "level": "GIALLO",
            "text": "L’area commerciale mostra potenziale ma richiede più metodo, conversione e continuità per sostenere la crescita.",
        })

    if not alerts:
        alerts.append({
            "level": "VERDE",
            "text": "Non emergono criticità dominanti: il focus ora è consolidare metodo, controllo e continuità esecutiva.",
        })

    if overall == "ROSSO":
        executive_summary = (
            "Il profilo emerso indica un business sotto pressione, con fragilità che richiedono priorità nette e interventi ravvicinati. "
            "La raccomandazione principale è rafforzare controllo, disciplina economica e prevedibilità operativa prima di spingere la crescita."
        )
    elif overall == "GIALLO":
        executive_summary = (
            "Il business mostra basi presenti ma ancora non sufficientemente consolidate. "
            "La priorità non è aumentare complessità, ma rendere più stabili cassa, margini ed esecuzione commerciale."
        )
    else:
        executive_summary = (
            "Il quadro generale è ordinato e relativamente solido. "
            "La fase successiva consiste nel consolidare i vantaggi già presenti e trasformarli in maggiore continuità e scalabilità."
        )

    if overall == "ROSSO":
        action_plan = [
            "Impostare un controllo finanziario settimanale con visibilità su cassa, incassi attesi e priorità di uscita.",
            "Ridurre dispersioni operative e proteggere margini prima di aumentare struttura o spesa commerciale.",
            "Semplificare il funnel commerciale e rendere obbligatori follow-up, prossimi step e criteri di priorità.",
        ]
    elif overall == "GIALLO":
        action_plan = [
            "Rendere più regolare il monitoraggio dei KPI chiave con una revisione manageriale ricorrente.",
            "Stabilizzare margini e conversione commerciale con maggiore disciplina su pricing, offerta e processo.",
            "Ridurre dipendenze da pochi fattori critici e costruire maggiore prevedibilità nelle attività di crescita.",
        ]
    else:
        action_plan = [
            "Consolidare la disciplina di controllo per mantenere chiara la lettura dei KPI chiave.",
            "Trasformare la stabilità attuale in routine gestionali replicabili e più scalabili.",
            "Usare gli scan periodici per verificare continuità, miglioramenti e nuovi punti di attenzione.",
        ]

    decisions = {
        "cash": (
            "Priorità: rafforzare visibilità sulla cassa, tempi di incasso e sostenibilità del breve periodo."
            if risk_cash >= 0.5
            else "Priorità: mantenere la disciplina finanziaria e prevenire future tensioni di cassa."
        ),
        "margini": (
            "Priorità: proteggere margini e struttura economica, evitando crescita che eroda redditività."
            if risk_margini >= 0.5
            else "Priorità: preservare la qualità economica attuale e renderla più ripetibile."
        ),
        "acq": (
            "Priorità: standardizzare il motore commerciale prima di aumentare pressione sulla crescita."
            if risk_acq >= 0.5
            else "Priorità: consolidare il funnel e migliorare continuità e resa dell’acquisizione."
        ),
    }

    return {
        "triade": {
            "meta": {
                "settore": inp.settore,
                "modello": inp.modello,
                "mese_riferimento": inp.mese_riferimento,
                "created_at": utc_now_iso(),
            },
            "state": {
                "overall": overall,
                "overall_score": overall_score,
                "confidenza": "MEDIA",
                "confidence": confidence,
                "summary": executive_summary,
                "risk_profile": risk_profile,
                "maturity_score": maturity_score,
                "maturity_label": maturity_label,
            },
            "risks": {
                "cash": round(risk_cash, 4),
                "margini": round(risk_margini, 4),
                "acq": round(risk_acq, 4),
            },
            "quiz": {
                "avg_risk": float(avg),
                "per_question": per_q,
            },
            "indicators": indicators,
            "alerts": alerts,
            "decisions": decisions,
            "action_plan": action_plan,
            "kpi": {
                "runway_mesi": None,
                "margine_pct": None,
                "conversione": None,
                "break_even_ratio": None,
                "burn_cash_ratio": None,
            },
        }
    }
