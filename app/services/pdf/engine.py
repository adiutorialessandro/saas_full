from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.pdfgen import canvas

from .config import PAGE_SIZE
from ..report_insights import report_header_payload
from .pages import render_one_pager, render_scan_pages
from .utils import clamp01
from .narrative import (
    benchmark_meta_payload,
    confidence_score,
    drivers_payload,
    hero_insight,
    plan_tasks_payload,
)


RISK_PROFILE_LABELS = {
    "cash": "Profilo di rischio: Finanziario",
    "margini": "Profilo di rischio: Economico-Marginale",
    "acq": "Profilo di rischio: Operativo-Commerciale",
}


OVERALL_LABELS = {
    "ROSSO": "Critical",
    "GIALLO": "Watchlist",
    "VERDE": "Healthy",
}



def _risk_value(value: Any, default: float = 0.5) -> float:
    v = clamp01(value, default)
    return float(v if v is not None else default)



def _risk_label(v: float | None) -> str:
    value = _risk_value(v, 0.5)

    if value >= 0.66:
        return "ROSSO"
    if value >= 0.33:
        return "GIALLO"
    return "VERDE"



def _triad_index(vm: Dict[str, Any]) -> float:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    cash = _risk_value(risks.get("cash"), 0.5)
    marg = _risk_value(risks.get("margini"), 0.5)
    acq = _risk_value(risks.get("acq"), 0.5)

    runway_mesi = kpi.get("runway_mesi")
    break_even_ratio = kpi.get("break_even_ratio")
    margine_pct = kpi.get("margine_pct")
    conversione = kpi.get("conversione")
    burn_cash_ratio = kpi.get("burn_cash_ratio")

    base_risk = (cash * 0.45) + (marg * 0.30) + (acq * 0.25)
    penalty = 0.0

    try:
        if runway_mesi is not None and float(runway_mesi) < 2:
            penalty += 0.12
    except Exception:
        pass

    try:
        if break_even_ratio is not None and float(break_even_ratio) < 1.0:
            penalty += 0.08
    except Exception:
        pass

    try:
        m = float(margine_pct)
        if m > 1:
            m /= 100.0
        if m < 0.30:
            penalty += 0.06
    except Exception:
        m = None

    try:
        c = float(conversione)
        if c > 1:
            c /= 100.0
        if c < 0.05:
            penalty += 0.05
    except Exception:
        c = None

    try:
        if burn_cash_ratio is not None:
            bcr = float(burn_cash_ratio)
            if bcr > 1:
                bcr /= 100.0
            if bcr > 0.25:
                penalty += 0.05
    except Exception:
        pass

    if m is not None and c is not None and m < 0.30 and c < 0.05:
        penalty += 0.06

    final_risk = min(1.0, base_risk + penalty)
    triad = round((1.0 - final_risk) * 100.0, 1)

    return max(0.0, min(100.0, triad))



def _risk_profile(cash_r: float, marg_r: float, acq_r: float) -> str:
    dominant = max(
        [
            ("cash", cash_r),
            ("margini", marg_r),
            ("acq", acq_r),
        ],
        key=lambda x: x[1],
    )[0]
    return RISK_PROFILE_LABELS[dominant]



def _build_ctx(scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Dict[str, Any]:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}
    indicators = vm.get("indicators") or []

    cash_r = _risk_value(risks.get("cash"), 0.5)
    marg_r = _risk_value(risks.get("margini"), 0.5)
    acq_r = _risk_value(risks.get("acq"), 0.5)

    delta = {
        "score": None,
        "cash": None,
        "margini": None,
        "acq": None,
    }

    triad = _triad_index(vm)
    overall = _risk_label(max(cash_r, marg_r, acq_r))
    risk_profile = vm.get("state", {}).get("risk_profile") or _risk_profile(cash_r, marg_r, acq_r)
    header_payload = report_header_payload(vm, delta)

    return {
        "settore": scan_meta.get("settore") or "Settore",
        "modello": scan_meta.get("modello") or "Business model",
        "mese": scan_meta.get("mese_riferimento") or "Periodo",
        "overall": overall,
        "overall_label": OVERALL_LABELS.get(overall, "Watchlist"),
        "triad": triad,
        "risk_profile": risk_profile,
        "confidence": confidence_score(vm),
        "summary": hero_insight(vm),
        "drivers": drivers_payload(vm),
        "benchmark_meta": benchmark_meta_payload(vm),
        "plan": plan_tasks_payload(vm),
        "cash_r": cash_r,
        "marg_r": marg_r,
        "acq_r": acq_r,
        "kpi": kpi,
        "indicators": indicators,
        "decisions": vm.get("decisions") or {},
        "board_note": vm.get("board_note"),
        "header_payload": header_payload,
        "diagnosis": header_payload.get("diagnosis") if isinstance(header_payload, dict) else {},
        "health": header_payload.get("health") if isinstance(header_payload, dict) else {},
    }



def generate_scan_pdf_enterprise(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = _build_ctx(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_scan_pages(c, ctx)
    c.save()
    return out_path



def generate_scan_pdf(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    return generate_scan_pdf_enterprise(out_path, scan_meta, vm)



def generate_report(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    return generate_scan_pdf_enterprise(out_path, scan_meta, vm)



def generate_one_pager(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = _build_ctx(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_one_pager(c, ctx)
    c.save()
    return out_path
