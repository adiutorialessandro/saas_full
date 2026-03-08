from __future__ import annotations

from typing import Any, Dict, List

from .utils import clamp01, dominant_risk


def hero_insight(vm: Dict[str, Any]) -> str:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    summary = str(state.get("summary") or "").strip()
    if summary:
        return summary

    dom = dominant_risk(risks)
    runway = kpi.get("runway_mesi")
    be = kpi.get("break_even_ratio")
    conv = kpi.get("conversione")

    parts: List[str] = [f"L’area prioritaria emersa dal report è {dom.lower()}."]
    try:
        if runway is not None:
            r = float(runway)
            parts.append(f"La runway attuale è pari a {r:.1f} mesi.")
            if r < 6:
                parts.append("Il margine di sicurezza finanziaria risulta limitato.")
    except Exception:
        pass

    try:
        if be is not None:
            b = float(be)
            if b < 1.10:
                parts.append("La copertura del break-even richiede attenzione per evitare vulnerabilità operative.")
    except Exception:
        pass

    try:
        if conv is not None:
            c = float(conv)
            if c > 1:
                c = c / 100.0
            parts.append(f"La conversione commerciale osservata è pari a {c * 100:.1f}%.")
    except Exception:
        pass

    parts.append("La priorità strategica è rendere più prevedibile la struttura economica e decisionale del business.")
    return " ".join(parts)


def confidence_score(vm: Dict[str, Any]) -> int:
    state = vm.get("state") or {}
    try:
        return int(state.get("confidence") or 0)
    except Exception:
        return 0


def data_quality(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, Any]:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    keys = [
        risks.get("cash"),
        risks.get("margini"),
        risks.get("acq"),
        kpi.get("runway_mesi"),
        kpi.get("break_even_ratio"),
        kpi.get("conversione"),
    ]
    present = sum(1 for v in keys if v is not None)
    completeness = int((present / 6.0) * 100)

    mese = str(scan_meta.get("mese_riferimento") or "").strip()
    recency = "OK" if mese and mese != "—" else "DA_VERIFICARE"

    flags: List[str] = []
    notes: List[str] = []

    if completeness >= 80:
        badge = "VERDE"
        label = "ALTA"
    elif completeness >= 50:
        badge = "GIALLO"
        label = "MEDIA"
    else:
        badge = "ROSSO"
        label = "BASSA"

    if recency != "OK":
        notes.append("Mese di riferimento non verificato.")

    if completeness < 80:
        notes.append("Dati essenziali presenti. Completa i campi opzionali per aumentare precisione e affidabilità.")

    return {
        "badge": badge,
        "label": label,
        "completeness": completeness,
        "completeness_score": completeness,
        "coherence_flags": flags,
        "recency": recency,
        "recency_flag": recency,
        "notes": notes,
    }


def definitions_payload(vm: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"name": "Runway", "formula": "Cassa / burn mensile", "unit": "mesi"},
        {"name": "Break-even ratio", "formula": "Incassi / ricavi di pareggio", "unit": "ratio"},
        {"name": "Conversione", "formula": "Clienti / lead", "unit": "%"},
        {"name": "Margine lordo", "formula": "(Ricavi − costi variabili) / ricavi", "unit": "%"},
        {"name": "Burn/Cash", "formula": "Burn mensile / cassa", "unit": "%"},
        {"name": "Triad Index™", "formula": "Media resilienza dei 3 pilastri", "unit": "0–100"},
    ]


def drivers_engine(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, List[str]]:
    kpi = vm.get("kpi") or {}
    risks = vm.get("risks") or {}

    cash: List[str] = []
    margins: List[str] = []
    acquisition: List[str] = []

    try:
        runway = kpi.get("runway_mesi")
        if runway is not None and float(runway) < 6:
            cash.append("Runway sotto soglia di sicurezza.")
    except Exception:
        pass

    try:
        be = kpi.get("break_even_ratio")
        if be is not None and float(be) < 1.10:
            margins.append("Copertura break-even troppo vicina alla soglia minima.")
    except Exception:
        pass

    try:
        conv = kpi.get("conversione")
        if conv is not None:
            c = float(conv)
            if c > 1:
                c = c / 100.0
            if c < 0.10:
                acquisition.append("Conversione commerciale inferiore al livello desiderabile.")
    except Exception:
        pass

    if not cash:
        cash = [
            "Approfondire disciplina di cassa, tempi di incasso e scadenziario.",
            "Verificare la pressione del breve periodo sulle uscite.",
            "Rendere più leggibile la dinamica tra cassa e burn mensile.",
        ]

    if not margins:
        margins = [
            "Approfondire pricing, struttura costi e qualità del mix offerta.",
            "Verificare la copertura dei costi fissi in rapporto ai ricavi.",
            "Ridurre dispersioni che comprimono il margine lordo.",
        ]

    if not acquisition:
        acquisition = [
            "Approfondire qualità lead, conversione e continuità della pipeline.",
            "Verificare la disciplina commerciale nei follow-up.",
            "Rendere più prevedibile il motore di acquisizione.",
        ]

    return {
        "cash": cash[:3],
        "margins": margins[:3],
        "acquisition": acquisition[:3],
    }


def benchmark_meta(vm: Dict[str, Any], settore: str) -> Dict[str, Any]:
    meta = vm.get("benchmark_meta") or {}
    enabled = bool(meta.get("enabled"))

    if not enabled:
        return {
            "enabled": False,
            "source": None,
            "sample_n": None,
            "sector_definition": None,
            "note": "Benchmark non disponibile: baseline provvisoria interna.",
        }

    return {
        "enabled": True,
        "source": meta.get("source") or "Dataset interno",
        "sample_n": meta.get("sample_n"),
        "sector_definition": meta.get("sector_definition") or settore,
        "note": meta.get("note") or "",
    }


def plan_tasks(vm: Dict[str, Any], kpi: Dict[str, Any]) -> List[Dict[str, Any]]:
    plan = vm.get("plan_tasks")
    if isinstance(plan, list) and plan:
        return plan

    runway = kpi.get("runway_mesi")
    conv = kpi.get("conversione")

    return [
        {
            "week": 1,
            "action": "Impostare un controllo finanziario settimanale con visibilità su cassa, incassi e priorità di uscita.",
            "owner": "CEO / Finance",
            "target_kpi": "Runway",
            "target_value": f">= 6 mesi (oggi {runway})" if runway is not None else ">= 6 mesi",
            "why": "Ridurre vulnerabilità nel breve periodo.",
        },
        {
            "week": 2,
            "action": "Rivedere pricing, scontistica e costi variabili per proteggere la qualità economica.",
            "owner": "Sales / Operations",
            "target_kpi": "Break-even ratio",
            "target_value": ">= 1.10",
            "why": "Rafforzare la sostenibilità dei margini.",
        },
        {
            "week": 3,
            "action": "Standardizzare pipeline, next step e follow-up per aumentare continuità commerciale.",
            "owner": "Sales Lead",
            "target_kpi": "Conversione",
            "target_value": f">= 10% (oggi {conv})" if conv is not None else ">= 10%",
            "why": "Rendere il motore di acquisizione più prevedibile.",
        },
        {
            "week": 4,
            "action": "Introdurre una review KPI breve e ricorrente con owner chiari e log decisionale.",
            "owner": "CEO",
            "target_kpi": "Confidence",
            "target_value": ">= 80%",
            "why": "Aumentare qualità decisionale e ripetibilità del controllo.",
        },
    ]


def drivers_payload(vm: Dict[str, Any]) -> Dict[str, List[str]]:
    return drivers_engine(vm, vm.get("meta") or {})


def benchmark_meta_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    return benchmark_meta(vm, str((vm.get("meta") or {}).get("settore") or "Settore"))


def plan_tasks_payload(vm: Dict[str, Any]) -> List[Dict[str, Any]]:
    return plan_tasks(vm, vm.get("kpi") or {})