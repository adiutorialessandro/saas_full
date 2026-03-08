from __future__ import annotations

from typing import Any, Dict, List

from .utils import clamp01, dominant_risk


def hero_insight(vm: Dict[str, Any]) -> str:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    dom = dominant_risk(risks)

    runway = kpi.get("runway_mesi")
    be = kpi.get("break_even_ratio")
    conv = kpi.get("conversione")
    burn = kpi.get("burn_pct")

    bits: List[str] = [f"Vincolo primario: {dom}."]

    if runway is not None:
        try:
            r = float(runway)
            bits.append(f"Runway: {r:.1f} mesi.")
            if r < 6:
                bits.append("Sotto soglia di sicurezza (6 mesi).")
        except Exception:
            pass

    if be is not None:
        try:
            b = float(be)
            bits.append(f"Break-even coverage: {b:.2f}.")
            if b < 1.10:
                bits.append("Margine di sicurezza limitato.")
        except Exception:
            pass

    if conv is not None:
        try:
            ccv = float(conv)
            if ccv > 1:
                ccv = ccv / 100.0
            bits.append(f"Conversione: {ccv*100:.1f}%.")
        except Exception:
            pass

    if burn is not None:
        try:
            bb = float(burn)
            if bb > 1 and bb <= 100:
                bb = bb / 100.0
            bits.append(f"Burn/Cash: {bb*100:.0f}%.")
        except Exception:
            pass

    bits.append("Implicazione: vulnerabilità a shock di liquidità nel breve periodo.")
    bits.append("Decisione: proteggere la cassa e congelare espansione finché runway ≥ 6 mesi.")
    return " ".join(bits)


def confidence_score(vm: Dict[str, Any]) -> int:
    required = [
        ("risks", "cash"),
        ("risks", "margini"),
        ("risks", "acq"),
        ("kpi", "runway_mesi"),
        ("kpi", "break_even_ratio"),
        ("kpi", "conversione"),
    ]
    missing = 0
    for root, key in required:
        obj = vm.get(root) or {}
        if obj.get(key) is None:
            missing += 1
    total = len(required)
    return max(0, int((1.0 - (missing / float(total))) * 100.0))


def data_quality(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Completeness + recency + coherence flags (+ notes)."""
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    keys = [
        ("risks.cash", risks.get("cash")),
        ("risks.margini", risks.get("margini")),
        ("risks.acq", risks.get("acq")),
        ("kpi.runway_mesi", kpi.get("runway_mesi")),
        ("kpi.break_even_ratio", kpi.get("break_even_ratio")),
        ("kpi.conversione", kpi.get("conversione")),
    ]
    present = sum(1 for _, v in keys if v is not None)
    completeness = int((present / len(keys)) * 100)

    flags: List[str] = []

    # Coherence heuristics (minime)
    try:
        m = clamp01(kpi.get("margine_pct"), default=None)
        if m is not None and (m < 0 or m > 1):
            flags.append("margine_pct fuori range")
    except Exception:
        pass

    # Recency flag
    mese = str(scan_meta.get("mese_riferimento") or "").strip()
    recency = "OK" if mese and mese != "—" else "DA_VERIFICARE"

    # Badge mapping
    # - >=80 => VERDE
    # - >=50 => se mese OK e nessuna anomalia => VERDE, altrimenti GIALLO
    # - <50  => ROSSO
    if completeness >= 80:
        badge = "VERDE"
        label = "ALTA"
    elif completeness >= 50:
        badge = "VERDE" if (recency == "OK" and not flags) else "GIALLO"
        label = "MEDIA"
    else:
        badge = "ROSSO"
        label = "BASSA"

    # Downgrade: se ci sono anomalie e risultava VERDE, scendi a GIALLO
    if flags and badge == "VERDE":
        badge, label = "GIALLO", "MEDIA"

    notes: List[str] = []

    # stime se presenti nel vm
    est_notes = []
    if (vm.get("kpi") or {}).get("dso_is_estimated"):
        est_notes.append("DSO stimato da quiz.")
    if (vm.get("kpi") or {}).get("incassi_is_estimated"):
        est_notes.append("Incassi stimati.")
    if est_notes:
        notes.append("STIME: " + " ".join(est_notes))

    if recency != "OK":
        notes.append("Mese di riferimento non verificato.")
    if flags:
        notes.append("Anomalie coerenza: " + ", ".join(flags[:3]))

    return {
        "badge": badge,
        "label": label,
        "completeness": completeness,
        "completeness_score": completeness,  # alias per compatibilità pagine
        "coherence_flags": flags,
        "recency": recency,
        "recency_flag": recency,
        "notes": notes,
    }

def definitions_payload(vm: Dict[str, Any]) -> List[Dict[str, str]]:
    """KPI definitions & formulas."""
    return [
        {"name": "Runway (mesi)", "formula": "Cassa / Burn mensile (burn = media ultimi 3 mesi)", "unit": "mesi"},
        {"name": "Net Cash Flow", "formula": "Incassi − (Variabili + Fissi + Marketing + Rate)", "unit": "€"},
        {"name": "Break-even coverage", "formula": "Margine contribuzione / Costi fissi (1.05=105%)", "unit": "ratio"},
        {"name": "Break-even ricavi", "formula": "Costi fissi / % contribuzione (se disponibile)", "unit": "€/mese"},
        {"name": "Conversione", "formula": "Clienti / Lead (lead = contatti qualificati)", "unit": "%"},
        {"name": "Margine lordo %", "formula": "(Ricavi − Variabili) / Ricavi", "unit": "%"},
        {"name": "Triad Index™", "formula": "Media resilienza dei 3 pilastri", "unit": "0–100"},
        {"name": "Rischio", "formula": "Score % criticità (0=ok, 100=critico)", "unit": "%"},
    ]


def drivers_engine(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, List[str]]:
    """Rule-based drivers. Output 3 bullet per area."""
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    cash_dr: List[str] = []
    marg_dr: List[str] = []
    acq_dr: List[str] = []

    runway = kpi.get("runway_mesi")
    ncf = kpi.get("net_cash_flow")
    dso = kpi.get("dso_giorni") or kpi.get("dso")
    rate_pct = kpi.get("rate_pct")

    be = kpi.get("break_even_ratio")
    contrib = kpi.get("contribuzione_pct") or kpi.get("margine_pct")
    fixed_over_rev = kpi.get("fissi_su_ricavi")

    conv = kpi.get("conversione")
    payback = kpi.get("payback_cac_mesi") or kpi.get("payback_cac")

    try:
        if runway is not None and float(runway) < 6:
            cash_dr.append("Runway sotto soglia → runway")
    except Exception:
        pass
    try:
        if ncf is not None and float(ncf) < 0:
            cash_dr.append("Burn > incassi → Net Cash Flow")
    except Exception:
        pass
    try:
        if dso is not None and float(dso) > 45:
            cash_dr.append("Incassi lenti (DSO alto/stimato) → cassa fragile (KPI: DSO)")
    except Exception:
        pass
    try:
        if rate_pct is not None and float(rate_pct) > 0.15:
            cash_dr.append("Debito/Rate incidono → cashflow compresso (KPI: rate%)")
    except Exception:
        pass

    try:
        if be is not None and float(be) < 1.10:
            marg_dr.append("Break-even troppo vicino → break-even coverage")
    except Exception:
        pass
    try:
        c = clamp01(contrib, default=None)
        if c is not None and c < 0.35:
            marg_dr.append("Contribuzione limitata → margine lordo %")
    except Exception:
        pass
    try:
        if fixed_over_rev is not None and float(fixed_over_rev) > 0.45:
            marg_dr.append("Struttura pesante (fissi/ricavi) → vulnerabilità margini (KPI: fissi/ricavi)")
    except Exception:
        pass

    try:
        cv = float(conv) if conv is not None else None
        if cv is not None:
            if cv > 1:
                cv = cv / 100.0
            if cv < 0.10:
                acq_dr.append("Conversione bassa → conversione")
    except Exception:
        pass
    # Payback CAC driver
    try:
        if payback is None:
            acq_dr.append("Payback CAC non stimato")
        else:
            if float(payback) > 6:
                acq_dr.append("Payback CAC > 6 → payback CAC")
    except Exception:
        pass
    try:
        acq_r = clamp01(risks.get("acq"), 0.5) or 0.5
        if acq_r > 0.60 and not acq_dr:
            acq_dr.append("Acquisizione fragile → serve playbook e tracking (KPI: rischio acquisizione)")
    except Exception:
        pass

    # Fill to 3 each with honest, NON-duplicated fallbacks
    cash_fallbacks = [
        "Driver da verificare: cash discipline / scadenziario / variabilità incassi.",
        "Driver da verificare: timing pagamenti fornitori / rate / picchi di costo.",
        "Driver da verificare: politiche incasso / anticipo / termini di pagamento.",
    ]
    marg_fallbacks = [
        "Driver da verificare: pricing e scontistica.",
        "Driver da verificare: mix prodotto/servizio e costi variabili.",
        "Driver da verificare: struttura costi fissi e capacità produttiva.",
    ]
    acq_fallbacks = [
        "Driver da verificare: qualità lead e fit (ICP).",
        "Driver da verificare: pipeline, next step e follow-up.",
        "Driver da verificare: canali, CAC e scalabilità.",
    ]

    for fb in cash_fallbacks:
        if len(cash_dr) >= 3:
            break
        if fb not in cash_dr:
            cash_dr.append(fb)

    for fb in marg_fallbacks:
        if len(marg_dr) >= 3:
            break
        if fb not in marg_dr:
            marg_dr.append(fb)

    for fb in acq_fallbacks:
        if len(acq_dr) >= 3:
            break
        if fb not in acq_dr:
            acq_dr.append(fb)

    # Safety: if still short for any reason, pad with a generic unique suffix
    while len(cash_dr) < 3:
        cash_dr.append(f"Driver da verificare: approfondimento richiesto sul fattore {len(cash_dr)+1}.")
    while len(marg_dr) < 3:
        marg_dr.append(f"Driver da verificare: approfondimento richiesto sul fattore {len(marg_dr)+1}.")
    while len(acq_dr) < 3:
        acq_dr.append(f"Driver da verificare: approfondimento richiesto sul fattore {len(acq_dr)+1}.")

    return {
        "cash": cash_dr[:3],
        "margins": marg_dr[:3],
        "acquisition": acq_dr[:3],
    }


def benchmark_meta(vm: Dict[str, Any], settore: str) -> Dict[str, Any]:
    """If you don't have a real source, keep it disabled."""
    meta = vm.get("benchmark_meta") or {}
    enabled = bool(meta.get("enabled", False))

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
        "source": meta.get("source") or "Dataset interno anonimo",
        "sample_n": meta.get("sample_n"),
        "sector_definition": meta.get("sector_definition") or settore,
        "note": meta.get("note") or "",
    }


def plan_tasks(vm: Dict[str, Any], kpi: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return 4 weekly tasks (task-based)."""
    plan = vm.get("plan_tasks")
    if isinstance(plan, list) and plan:
        return plan

    # Default plan
    runway = kpi.get("runway_mesi")
    conv = kpi.get("conversione")

    return [
        {
            "week": 1,
            "action": "Cash discipline: forecast settimanale + stop spese non essenziali + scadenziario incassi.",
            "owner": "CEO/Finance",
            "target_kpi": "Runway",
            "target_value": f">= 6 mesi (oggi {runway})" if runway is not None else ">= 6 mesi",
            "why": "Ridurre rischio shock di liquidità nel breve.",
        },
        {
            "week": 2,
            "action": "Margini: revisione listino + stop sconti non autorizzati + controllo costi variabili per SKU/servizio.",
            "owner": "Ops/Commerciale",
            "target_kpi": "BE coverage",
            "target_value": ">= 1.10",
            "why": "Aumentare copertura costi fissi e margine di sicurezza.",
        },
        {
            "week": 3,
            "action": "Funnel: standardizza pipeline + next step obbligatorio + follow-up cadenzato (SLA) + tracking.",
            "owner": "Sales Lead",
            "target_kpi": "Conversione",
            "target_value": f">= 10% (oggi {conv})" if conv is not None else ">= 10%",
            "why": "Ridurre dispersione lead e aumentare closing.",
        },
        {
            "week": 4,
            "action": "Ciclo decisionale: KPI review 30' settimanale + owner per metrica + log decisioni.",
            "owner": "CEO",
            "target_kpi": "Confidence",
            "target_value": ">= 80%",
            "why": "Rendere il report difendibile e ripetibile.",
        },
    ]


def drivers_payload(vm: Dict[str, Any]) -> Dict[str, List[str]]:
    """Rule-based drivers: 3 bullet per triade."""
    k = vm.get("kpi") or {}
    r = vm.get("risks") or {}

    runway = k.get("runway_mesi")
    ncf = k.get("net_cash_flow")
    dso = k.get("dso")
    contrib = k.get("contribuzione_pct") or k.get("margine_pct")
    fixed_on_rev = k.get("fissi_su_ricavi")
    rate_on_contrib = k.get("rate_su_contribuzione")
    payback = k.get("payback_cac_mesi")
    conv = k.get("conversione")

    def add(arr, text):
        if text and len(arr) < 3:
            arr.append(text)

    cash, margins, acq = [], [], []

    # CASSA
    try:
        if runway is not None and float(runway) < 1:
            add(cash, "Burn > incassi (runway < 1 mese) → runway_mesi")
    except Exception:
        pass
    try:
        if ncf is not None and float(ncf) < 0:
            add(cash, "Cash flow negativo → net_cash_flow")
    except Exception:
        pass
    if (k.get("dso_is_estimated") or False) and dso is not None:
        add(cash, "Incassi lenti (DSO stimato) → dso")
    elif dso is not None:
        add(cash, "Incassi lenti (DSO) → dso")
    if rate_on_contrib is not None:
        add(cash, "Debito che morde (rate su contribuzione) → rate_su_contribuzione")

    # MARGINI
    if contrib is not None:
        add(margins, "Contribuzione insufficiente → contribuzione_pct / margine_pct")
    if fixed_on_rev is not None:
        add(margins, "Struttura pesante (fissi su ricavi) → fissi_su_ricavi")
    if k.get("variabili_su_ricavi") is not None:
        add(margins, "Variabili alti su ricavi → variabili_su_ricavi")

    # ACQUISIZIONE
    if payback is not None:
        try:
            if float(payback) > 6:
                add(acq, "Acquisizione non sostenibile (payback CAC > 6) → payback_cac_mesi")
            else:
                add(acq, "Payback CAC migliorabile → payback_cac_mesi")
        except Exception:
            pass
    if conv is not None:
        try:
            if float(conv) < 0.08:
                add(acq, "Funnel/follow-up inefficiente (conversione bassa) → conversione")
            else:
                add(acq, "Conversione ok ma scalabilità da verificare → conversione")
        except Exception:
            pass
    if k.get("lead") is not None and k.get("clienti") is not None:
        add(acq, "Volume lead/clienti da stabilizzare → lead, clienti")

    # fallback se vuoti
    if not cash:
        cash = ["Driver non ancora determinabile con precisione: completa i KPI cash per una spiegazione più affidabile."]
    if not margins:
        margins = ["Driver non ancora determinabile con precisione: completa i KPI margini per una spiegazione più affidabile."]
    if not acq:
        acq = ["Driver non ancora determinabile con precisione: completa i KPI acquisizione per una spiegazione più affidabile."]

    return {"cash": cash[:3], "margins": margins[:3], "acquisition": acq[:3]}


def benchmark_meta_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    """Benchmark metadata. If missing, disable radar."""
    b = (vm.get("benchmark") or {})
    enabled = bool(b.get("enabled")) and bool(b.get("source")) and bool(b.get("sample_n")) and bool(b.get("sector_definition"))
    if not enabled:
        return {
            "enabled": False,
            "source": "",
            "sample_n": "",
            "sector_definition": "",
            "note": "Benchmark non disponibile: baseline provvisoria interna.",
        }
    return {
        "enabled": True,
        "source": str(b.get("source")),
        "sample_n": str(b.get("sample_n")),
        "sector_definition": str(b.get("sector_definition")),
        "note": str(b.get("note") or ""),
    }


def plan_tasks_payload(vm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Piano operativo a 90 giorni (4 settimane)."""
    # se vm già contiene tasks, usali
    pre = (vm.get("plan_tasks") or [])
    if isinstance(pre, list) and pre:
        return pre[:8]

    # fallback generico ma eseguibile
    return [
        {"week": 1, "action": "Raccogli dati base (ricavi, incassi, fissi, variabili) + allinea definizioni KPI.", "owner": "CEO/CFO", "target_kpi": "Completezza", "target_value": ">=80%", "why": "Aumenta confidenza e difendibilità."},
        {"week": 2, "action": "Riduci burn: taglio/renegoziazione 1–2 voci fisse + piano incassi su crediti.", "owner": "CEO", "target_kpi": "Net Cash Flow", "target_value": ">=0", "why": "Stabilizza cassa."},
        {"week": 3, "action": "Intervento margini: repricing o mix servizi + controllo variabili.", "owner": "Sales/Ops", "target_kpi": "Break-even coverage", "target_value": ">=1.05", "why": "Copre i fissi in modo sostenibile."},
        {"week": 4, "action": "Sistema acquisizione: pipeline + follow-up + 1 esperimento CAC/Conversione.", "owner": "Sales/Marketing", "target_kpi": "Conversione", "target_value": "+20% vs baseline", "why": "Rende scalabile l’acquisizione."},
    ]
