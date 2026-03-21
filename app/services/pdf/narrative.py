"""
SaaS Full - Narrative & Content Generation (PDF)
"""
from typing import Dict, Any, List

def confidence_score(vm: Dict[str, Any]) -> int:
    return int(vm.get("state", {}).get("confidence", 50))

def hero_insight(vm: Dict[str, Any]) -> str:
    return vm.get("state", {}).get("summary", "Analisi del business completata.")

def benchmark_meta_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    bench_results = vm.get("benchmark_results") or {}
    bench_raw = vm.get("benchmark_raw") or {}
    meta = vm.get("meta") or {}
    bench_meta = meta.get("benchmark_settore") or {}

    if bench_results or bench_meta:
        return {
            "available": True,
            "sector": bench_meta.get("settore_riferimento") or meta.get("settore") or "Media Standard",
            "runway_target": bench_results.get("runway", {}).get("target") or bench_raw.get("runway_mesi") or bench_meta.get("runway_target"),
            "margine_target": bench_results.get("margine", {}).get("target") or bench_raw.get("margine_pct") or bench_meta.get("margine_target"),
            "conversione_target": bench_results.get("conversione", {}).get("target") or bench_raw.get("conversione") or bench_meta.get("conversione_target"),
            "be_target": bench_results.get("break_even", {}).get("target") or bench_raw.get("break_even_ratio") or bench_meta.get("be_target"),
        }

    return {"available": False, "sector": None, "runway_target": None, "margine_target": None, "conversione_target": None, "be_target": None}

def drivers_payload(vm: Dict[str, Any]) -> Dict[str, List[str]]:
    drv = vm.get("drivers")
    if isinstance(drv, dict):
        def _fmt(lst):
            return [(f"{d.get('title', '')}: {d.get('text', '')}".strip(": ")) if isinstance(d, dict) else str(d) for d in (lst or [])]
        return {"cash": _fmt(drv.get("cash")), "margins": _fmt(drv.get("margins") or drv.get("margini")), "acq": _fmt(drv.get("acq"))}

    decisions = vm.get("decisions", {})
    kpi = vm.get("kpi", {})

    cash, margins, acq = [], [], []
    cash.append(f"Runway e liquidità: {decisions.get('cash', 'Monitorare la cassa.')}")
    if kpi.get("runway_mesi") is not None: cash.append(f"Runway attuale: {round(float(kpi.get('runway_mesi')), 1)} mesi.")
    
    margins.append(f"Marginalità: {decisions.get('margini', 'Proteggere il margine lordo.')}")
    if kpi.get("margine_pct") is not None: margins.append(f"Margine lordo attuale: {round(float(kpi.get('margine_pct')) * (100 if float(kpi.get('margine_pct')) <= 1 else 1), 1)}%.")
    
    acq.append(f"Motore commerciale: {decisions.get('acq', 'Rendere acquisizione prevedibile.')}")
    if kpi.get("conversione") is not None: acq.append(f"Conversione attuale: {round(float(kpi.get('conversione')) * (100 if float(kpi.get('conversione')) <= 1 else 1), 1)}%.")

    return {"cash": cash, "margins": margins, "acq": acq}

def plan_tasks_payload(vm: Dict[str, Any]) -> List[Dict[str, str]]:
    existing = vm.get("plan_tasks")
    if isinstance(existing, list) and existing and isinstance(existing[0], dict): return existing

    action_plan = vm.get("action_plan", [])
    if not action_plan:
        return [{"week": "1", "action": "Impostare controllo dei KPI.", "owner": "CEO", "target_kpi": "Score", "target_value": "Migliorare report"}]

    return [{"week": str(idx + 1), "action": str(action), "owner": "Management", "target_kpi": "KPI", "target_value": "Migliorare"} for idx, action in enumerate(action_plan[:4])]