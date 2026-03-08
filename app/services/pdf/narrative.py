from __future__ import annotations

from typing import Any, Dict, List

from .utils import clamp01, fmt_num, fmt_pct


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _normalize_ratio(value: Any) -> float | None:
    v = _safe_float(value, None)
    if v is None:
        return None
    if v > 1.0:
        return v / 100.0
    return v


def _risk_label_from_value(value: Any) -> str:
    v = clamp01(value, 0.5) or 0.5
    if v >= 0.66:
        return "alto"
    if v >= 0.33:
        return "medio"
    return "contenuto"


def _dominant_area(risks: Dict[str, Any]) -> str:
    cash = clamp01((risks or {}).get("cash"), 0.5) or 0.5
    margini = clamp01((risks or {}).get("margini"), 0.5) or 0.5
    acq = clamp01((risks or {}).get("acq"), 0.5) or 0.5

    return max(
        [
            ("cassa", cash),
            ("margini", margini),
            ("acquisizione", acq),
        ],
        key=lambda x: x[1],
    )[0]


def confidence_score(vm: Dict[str, Any]) -> int:
    state = vm.get("state") or {}
    try:
        return int(float(state.get("confidence") or 0))
    except Exception:
        return 0


def hero_insight(vm: Dict[str, Any]) -> str:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    existing = str(state.get("summary") or "").strip()
    if existing:
        return existing

    area = _dominant_area(risks)
    runway = _safe_float(kpi.get("runway_mesi"), None)
    break_even = _safe_float(kpi.get("break_even_ratio"), None)
    conversione = _normalize_ratio(kpi.get("conversione"))
    margine = _normalize_ratio(kpi.get("margine_pct"))

    parts: List[str] = []

    if area == "cassa":
        parts.append(
            "Il quadro emerso evidenzia una priorità finanziaria: la stabilità del business dipende soprattutto dalla capacità di rendere più leggibili cassa, incassi e margine di sicurezza di breve periodo."
        )
    elif area == "margini":
        parts.append(
            "Il vincolo principale appare economico: la priorità non è aumentare volume, ma proteggere redditività, pricing e qualità del mix di offerta."
        )
    else:
        parts.append(
            "L’area più esposta è commerciale: il business richiede maggiore continuità nella generazione di domanda, nella conversione e nella prevedibilità della pipeline."
        )

    if runway is not None:
        if runway < 4:
            parts.append(
                f"La runway stimata è pari a {fmt_num(runway, 1, ' mesi')}, un livello che suggerisce presidio ravvicinato del cashflow e priorità molto selettive."
            )
        elif runway < 6:
            parts.append(
                f"La runway stimata è pari a {fmt_num(runway, 1, ' mesi')}: esiste operatività, ma il margine di sicurezza resta limitato."
            )

    if break_even is not None and break_even < 1.10:
        parts.append(
            "La copertura del break-even non è ancora sufficientemente ampia: servono maggiore disciplina economica e protezione dei margini."
        )

    if conversione is not None and conversione < 0.10:
        parts.append(
            f"La conversione osservata ({fmt_pct(conversione, 1)}) indica spazio di miglioramento nella qualità del funnel e nella gestione dei passaggi commerciali."
        )

    if margine is not None and margine < 0.40:
        parts.append(
            f"Il margine lordo ({fmt_pct(margine, 1)}) richiede attenzione per evitare crescita a bassa qualità economica."
        )

    parts.append(
        "La priorità strategica è trasformare la lettura attuale in un sistema di decisione più prevedibile, con owner chiari, KPI ricorrenti e minore dispersione operativa."
    )

    return " ".join(parts)


def data_quality(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, Any]:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    values = [
        risks.get("cash"),
        risks.get("margini"),
        risks.get("acq"),
        kpi.get("runway_mesi"),
        kpi.get("break_even_ratio"),
        kpi.get("conversione"),
    ]
    present = sum(1 for v in values if v is not None)
    completeness = int((present / 6.0) * 100)

    mese = str(scan_meta.get("mese_riferimento") or "").strip()
    recency = "OK" if mese and mese != "—" else "DA_VERIFICARE"

    notes: List[str] = []
    flags: List[str] = []

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
        notes.append("Il mese di riferimento non risulta valorizzato in modo completo.")

    if completeness < 80:
        notes.append(
            "I dati essenziali sono presenti, ma un set KPI più completo aumenterebbe precisione, difendibilità e qualità delle decisioni."
        )

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
        {
            "name": "Runway",
            "formula": "Cassa disponibile / burn mensile",
            "unit": "mesi",
        },
        {
            "name": "Break-even ratio",
            "formula": "Incassi / ricavi di pareggio",
            "unit": "ratio",
        },
        {
            "name": "Conversione",
            "formula": "Clienti acquisiti / lead generati",
            "unit": "%",
        },
        {
            "name": "Margine lordo",
            "formula": "(Ricavi − costi variabili) / ricavi",
            "unit": "%",
        },
        {
            "name": "Burn/Cash",
            "formula": "Burn mensile / cassa disponibile",
            "unit": "%",
        },
        {
            "name": "Triad Index™",
            "formula": "Indice sintetico di resilienza dei tre pilastri",
            "unit": "0–100",
        },
    ]


def drivers_engine(vm: Dict[str, Any], scan_meta: Dict[str, Any]) -> Dict[str, List[str]]:
    kpi = vm.get("kpi") or {}
    risks = vm.get("risks") or {}

    runway = _safe_float(kpi.get("runway_mesi"), None)
    be = _safe_float(kpi.get("break_even_ratio"), None)
    conv = _normalize_ratio(kpi.get("conversione"))
    margine = _normalize_ratio(kpi.get("margine_pct"))
    burn_cash = _normalize_ratio(kpi.get("burn_cash_ratio"))

    cash_dr: List[str] = []
    marg_dr: List[str] = []
    acq_dr: List[str] = []

    if runway is not None:
        if runway < 4:
            cash_dr.append("Runway sotto soglia di sicurezza: la visibilità di breve richiede presidio ravvicinato.")
        elif runway < 6:
            cash_dr.append("Runway presente ma ancora limitata: opportuno rafforzare il margine di sicurezza finanziaria.")

    if burn_cash is not None:
        if burn_cash > 0.25:
            cash_dr.append("Il rapporto burn/cash indica una pressione significativa sulla liquidità disponibile.")
        elif burn_cash > 0.12:
            cash_dr.append("La pressione del burn sulla cassa è da monitorare con maggiore frequenza.")

    if be is not None:
        if be < 1.0:
            marg_dr.append("Gli incassi non coprono ancora in modo pieno il punto di pareggio.")
        elif be < 1.10:
            marg_dr.append("La copertura del break-even è troppo vicina alla soglia minima di sicurezza.")

    if margine is not None:
        if margine < 0.30:
            marg_dr.append("Il margine lordo è basso rispetto a una struttura economicamente protetta.")
        elif margine < 0.40:
            marg_dr.append("Il margine lordo è presente ma richiede maggiore disciplina su pricing e costi.")

    if conv is not None:
        if conv < 0.05:
            acq_dr.append("La conversione commerciale è debole e suggerisce revisione di offerta, target e follow-up.")
        elif conv < 0.10:
            acq_dr.append("La conversione è migliorabile: la pipeline non appare ancora sufficientemente prevedibile.")

    cash_r = clamp01(risks.get("cash"), 0.5) or 0.5
    marg_r = clamp01(risks.get("margini"), 0.5) or 0.5
    acq_r = clamp01(risks.get("acq"), 0.5) or 0.5

    if not cash_dr:
        if cash_r >= 0.66:
            cash_dr = [
                "La struttura finanziaria richiede maggiore frequenza di controllo e visibilità di breve.",
                "È prioritario rendere più leggibili incassi attesi, scadenze e disponibilità effettiva.",
                "La gestione di cassa va trasformata in routine manageriale, non in verifica occasionale.",
            ]
        elif cash_r >= 0.33:
            cash_dr = [
                "La situazione di cassa è operativa ma non ancora abbastanza protetta.",
                "Serve maggiore disciplina nella pianificazione delle uscite e nella previsione degli incassi.",
                "Una review settimanale del cashflow migliorerebbe qualità e tempestività delle decisioni.",
            ]
        else:
            cash_dr = [
                "La tenuta finanziaria appare relativamente ordinata.",
                "Il passo successivo è consolidare la disciplina di monitoraggio senza abbassare la soglia di attenzione.",
                "La leggibilità del breve periodo può diventare un vantaggio gestionale stabile.",
            ]

    if not marg_dr:
        if marg_r >= 0.66:
            marg_dr = [
                "La qualità economica del business appare esposta a erosione.",
                "Il mix tra prezzi, costi e priorità commerciali richiede riallineamento.",
                "È necessario proteggere i margini prima di aumentare complessità o volume.",
            ]
        elif marg_r >= 0.33:
            marg_dr = [
                "I margini risultano presenti ma non ancora pienamente difesi.",
                "Serve maggiore disciplina su sconti, costi e qualità della proposta.",
                "Una crescita sana richiede più protezione della redditività unitaria.",
            ]
        else:
            marg_dr = [
                "La tenuta economica appare relativamente stabile.",
                "L’obiettivo ora è consolidare la qualità del margine e renderla più ripetibile.",
                "Prezzi, mix e costi possono diventare leva di rafforzamento, non solo controllo.",
            ]

    if not acq_dr:
        if acq_r >= 0.66:
            acq_dr = [
                "Il motore commerciale non appare ancora sufficientemente stabile o ripetibile.",
                "La crescita dipende troppo da iniziative episodiche o da esecuzione non standardizzata.",
                "È prioritario strutturare funnel, passaggi decisionali e responsabilità commerciali.",
            ]
        elif acq_r >= 0.33:
            acq_dr = [
                "L’area commerciale mostra potenziale ma richiede più metodo e continuità.",
                "La pipeline deve diventare più leggibile, governabile e misurabile.",
                "La conversione può migliorare con processi più disciplinati e ownership più chiara.",
            ]
        else:
            acq_dr = [
                "L’acquisizione appare sufficientemente attiva e ordinata.",
                "Il passo successivo è aumentare prevedibilità e resa senza disperdere energia commerciale.",
                "La crescita può essere resa più replicabile con review e KPI più rigorosi.",
            ]

    return {
        "cash": cash_dr[:3],
        "margins": marg_dr[:3],
        "acquisition": acq_dr[:3],
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
            "note": "Benchmark non disponibile per questo report. La lettura comparativa è stata sostituita da una baseline interna prudenziale.",
        }

    return {
        "enabled": True,
        "source": meta.get("source") or "Dataset interno",
        "sample_n": meta.get("sample_n"),
        "sector_definition": meta.get("sector_definition") or settore,
        "note": meta.get("note") or "Benchmark disponibile su campione comparabile.",
    }


def plan_tasks(vm: Dict[str, Any], kpi: Dict[str, Any]) -> List[Dict[str, Any]]:
    provided = vm.get("plan_tasks")
    if isinstance(provided, list) and provided:
        return provided

    runway = _safe_float(kpi.get("runway_mesi"), None)
    conv = _normalize_ratio(kpi.get("conversione"))
    be = _safe_float(kpi.get("break_even_ratio"), None)

    runway_now = fmt_num(runway, 1, " mesi") if runway is not None else "n.d."
    conv_now = fmt_pct(conv, 1) if conv is not None else "n.d."
    be_now = fmt_num(be, 2) if be is not None else "n.d."

    return [
        {
            "week": 1,
            "action": "Impostare un controllo settimanale di cassa con visibilità su incassi attesi, uscite prioritarie e scostamenti.",
            "owner": "CEO / Finance",
            "target_kpi": "Runway",
            "target_value": f"Portare la runway verso una soglia > 6 mesi (attuale: {runway_now})",
            "why": "Rafforzare il margine di sicurezza di breve periodo.",
        },
        {
            "week": 2,
            "action": "Rivedere pricing, marginalità per linea e qualità del mix offerta per proteggere la redditività.",
            "owner": "CEO / Sales",
            "target_kpi": "Break-even ratio",
            "target_value": f"Portare il break-even ratio sopra 1.10 (attuale: {be_now})",
            "why": "Ridurre la vulnerabilità economica della struttura.",
        },
        {
            "week": 3,
            "action": "Standardizzare pipeline, criteri di qualifica e follow-up per aumentare continuità commerciale.",
            "owner": "Sales Lead",
            "target_kpi": "Conversione",
            "target_value": f"Portare la conversione ad almeno 10% (attuale: {conv_now})",
            "why": "Rendere il motore di acquisizione più prevedibile e ripetibile.",
        },
        {
            "week": 4,
            "action": "Introdurre una review KPI breve, ricorrente e con owner chiari per trasformare il controllo in abitudine manageriale.",
            "owner": "CEO",
            "target_kpi": "Confidence",
            "target_value": "Stabilizzare la qualità informativa del report oltre l’80%",
            "why": "Aumentare qualità decisionale, ritmo esecutivo e allineamento interno.",
        },
    ]


def drivers_payload(vm: Dict[str, Any]) -> Dict[str, List[str]]:
    meta = vm.get("meta") or {}
    return drivers_engine(vm, meta)


def benchmark_meta_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    meta = vm.get("meta") or {}
    settore = str(meta.get("settore") or "Settore")
    return benchmark_meta(vm, settore)


def plan_tasks_payload(vm: Dict[str, Any]) -> List[Dict[str, Any]]:
    return plan_tasks(vm, vm.get("kpi") or {})