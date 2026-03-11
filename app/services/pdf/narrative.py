from typing import Dict, Any, List


def confidence_score(vm: Dict[str, Any]) -> int:
    state = vm.get("state") or {}
    return int(state.get("confidence") or 50)


def hero_insight(vm: Dict[str, Any]) -> str:
    state = vm.get("state") or {}
    return state.get("summary") or "Analisi del business completata."


def benchmark_meta_payload(vm: Dict[str, Any]) -> Dict[str, Any]:
    bench_results = vm.get("benchmark_results") or {}
    bench_raw = vm.get("benchmark_raw") or {}
    meta = vm.get("meta") or {}
    bench_meta = meta.get("benchmark_settore") or {}

    if bench_results:
        return {
            "available": True,
            "sector": bench_meta.get("settore_riferimento") or meta.get("settore") or "Media Standard",
            "runway_target": bench_results.get("runway", {}).get("target") or bench_raw.get("runway_mesi"),
            "margine_target": bench_results.get("margine", {}).get("target") or bench_raw.get("margine_pct"),
            "conversione_target": bench_results.get("conversione", {}).get("target") or bench_raw.get("conversione"),
            "be_target": bench_results.get("break_even", {}).get("target") or bench_raw.get("break_even_ratio"),
        }

    if bench_meta:
        return {
            "available": True,
            "sector": bench_meta.get("settore_riferimento") or "Media Standard",
            "runway_target": bench_meta.get("runway_target"),
            "margine_target": bench_meta.get("margine_target"),
            "conversione_target": bench_meta.get("conversione_target"),
            "be_target": bench_meta.get("be_target"),
        }

    return {
        "available": False,
        "sector": None,
        "runway_target": None,
        "margine_target": None,
        "conversione_target": None,
        "be_target": None,
    }


def _driver_item(title: str, text: str) -> str:
    return f"{title}: {text}"


def drivers_payload(vm: Dict[str, Any]) -> Dict[str, List[str]]:
    drv = vm.get("drivers")

    if isinstance(drv, dict):
        def _fmt_list(lst):
            out = []
            for d in (lst or []):
                if isinstance(d, dict):
                    title = d.get("title") or ""
                    text = d.get("text") or ""
                    out.append(f"{title}: {text}".strip(": "))
                else:
                    out.append(str(d))
            return out

        return {
            "cash": _fmt_list(drv.get("cash")),
            "margins": _fmt_list(drv.get("margins") or drv.get("margini")),
            "acq": _fmt_list(drv.get("acq")),
        }

    decisions = vm.get("decisions") or {}
    kpi = vm.get("kpi") or {}

    cash_items = [
        _driver_item(
            "Runway e liquidità",
            decisions.get("cash")
            or "Monitorare la cassa e aumentare la visibilità sugli incassi attesi.",
        )
    ]

    if kpi.get("runway_mesi") is not None:
        cash_items.append(
            _driver_item(
                "Runway attuale",
                f"Runway disponibile: {round(float(kpi.get('runway_mesi')), 1)} mesi.",
            )
        )

    margins_items = [
        _driver_item(
            "Marginalità e break-even",
            decisions.get("margini")
            or "Proteggere il margine lordo e migliorare la disciplina economica.",
        )
    ]

    if kpi.get("margine_pct") is not None:
        m = float(kpi.get("margine_pct"))
        if m <= 1:
            m *= 100
        margins_items.append(
            _driver_item(
                "Margine lordo",
                f"Margine lordo attuale: {round(m, 1)}%.",
            )
        )

    acq_items = [
        _driver_item(
            "Motore commerciale",
            decisions.get("acq")
            or "Rendere l'acquisizione più prevedibile e replicabile.",
        )
    ]

    if kpi.get("conversione") is not None:
        c = float(kpi.get("conversione"))
        if c <= 1:
            c *= 100
        acq_items.append(
            _driver_item(
                "Conversione",
                f"Conversione attuale: {round(c, 1)}%.",
            )
        )

    return {
        "cash": cash_items,
        "margins": margins_items,
        "acq": acq_items,
    }


def plan_tasks_payload(vm: Dict[str, Any]) -> List[Dict[str, str]]:
    existing = vm.get("plan_tasks")
    if isinstance(existing, list) and existing and isinstance(existing[0], dict):
        return existing

    action_plan = vm.get("action_plan") or []
    kpi = vm.get("kpi") or {}
    bench_results = vm.get("benchmark_results") or {}

    defaults = [
        {
            "week": "1",
            "owner": "CEO / Finance",
            "target_kpi": "Runway",
            "target_value": (
                f"Portare la runway verso {bench_results.get('runway', {}).get('target', 6)} mesi"
                if bench_results.get("runway")
                else "Rafforzare la visibilità di cassa"
            ),
        },
        {
            "week": "2",
            "owner": "CEO / Sales",
            "target_kpi": "Margine lordo",
            "target_value": (
                f"Avvicinare il margine al target {round((bench_results.get('margine', {}).get('target', 0.55) * 100), 1)}%"
                if bench_results.get("margine")
                else "Difendere la marginalità"
            ),
        },
        {
            "week": "3",
            "owner": "Sales Lead",
            "target_kpi": "Conversione",
            "target_value": (
                f"Avvicinare la conversione al target {round((bench_results.get('conversione', {}).get('target', 0.10) * 100), 1)}%"
                if bench_results.get("conversione")
                else "Aumentare la conversione"
            ),
        },
        {
            "week": "4",
            "owner": "CEO",
            "target_kpi": "Break-even ratio",
            "target_value": (
                f"Portare il break-even ratio sopra {bench_results.get('break_even', {}).get('target', 1.2)}"
                if bench_results.get("break_even")
                else "Rafforzare il break-even"
            ),
        },
    ]

    rows: List[Dict[str, str]] = []

    for idx, action in enumerate(action_plan[:4]):
        meta = defaults[idx] if idx < len(defaults) else {
            "week": str(idx + 1),
            "owner": "Management",
            "target_kpi": "KPI chiave",
            "target_value": "Migliorare la performance",
        }

        rows.append(
            {
                "week": meta["week"],
                "action": str(action),
                "owner": meta["owner"],
                "target_kpi": meta["target_kpi"],
                "target_value": meta["target_value"],
            }
        )

    if not rows:
        rows = [
            {
                "week": "1",
                "action": "Impostare un controllo settimanale dei KPI.",
                "owner": "CEO",
                "target_kpi": "Business Stability Score",
                "target_value": "Aumentare affidabilità e tracciabilità del report",
            }
        ]

    return rows
