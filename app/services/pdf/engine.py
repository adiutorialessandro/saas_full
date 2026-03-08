from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

from reportlab.pdfgen import canvas

from .config import BRAND_NAME, PAGE_SIZE
from .narrative import (
    benchmark_meta,
    confidence_score,
    data_quality,
    definitions_payload,
    drivers_engine,
    hero_insight,
    plan_tasks,
)
from .pages import render_one_pager, render_scan_pages
from .utils import clamp01, now_str, safe_float


def _build_context(scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Dict[str, Any]:
    state = vm.get("state") or {}
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}

    settore = scan_meta.get("settore", "—")
    modello = scan_meta.get("modello", "—")
    mese = scan_meta.get("mese_riferimento", "—")
    created_at = scan_meta.get("created_at") or now_str()
    scan_id = str(scan_meta.get("id", "—"))

    cash_r = clamp01(risks.get("cash"), 0.5) or 0.5
    marg_r = clamp01(risks.get("margini"), 0.5) or 0.5
    acq_r = clamp01(risks.get("acq"), 0.5) or 0.5

    overall = str(state.get("overall") or "GIALLO").upper()
    triad = safe_float(state.get("overall_score"), 50.0) or 50.0
    confidence = int(safe_float(state.get("confidence"), confidence_score(vm)) or 0)

    summary = str(state.get("summary") or hero_insight(vm)).strip()
    risk_profile = str(state.get("risk_profile") or "Profilo di rischio: Non disponibile")
    maturity_label = str(state.get("maturity_label") or "Maturità: Non disponibile")
    board_note = str(state.get("board_note") or "Documento sintetico a supporto delle decisioni prioritarie del management.")

    defs = definitions_payload(vm)
    dq = data_quality(vm, scan_meta)
    drivers = drivers_engine(vm, scan_meta)
    plan = plan_tasks(vm, kpi)
    bm = benchmark_meta(vm, settore)

    return {
        "brand_name": BRAND_NAME,
        "scan_meta": scan_meta,
        "vm": vm,
        "state": state,
        "risks": risks,
        "kpi": kpi,
        "decisions": vm.get("decisions") or {},
        "action_plan": vm.get("action_plan") or [],
        "alerts": vm.get("alerts") or [],
        "indicators": vm.get("indicators") or [],
        "definitions": defs,
        "data_quality": dq,
        "drivers": drivers,
        "plan": plan,
        "benchmark_meta": bm,
        "settore": settore,
        "modello": modello,
        "mese": mese,
        "created_at": created_at,
        "scan_id": scan_id,
        "overall": overall,
        "triad": triad,
        "confidence": confidence,
        "summary": summary,
        "risk_profile": risk_profile,
        "maturity_label": maturity_label,
        "board_note": board_note,
        "cash_r": cash_r,
        "marg_r": marg_r,
        "acq_r": acq_r,
    }


def generate_report(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
    template: str = "saas_scan_v1",
) -> Path:
    template = (template or "saas_scan_v1").strip().lower()
    if template == "saas_scan_v1":
        return generate_scan_pdf_enterprise(out_path, scan_meta, vm)
    if template == "one_pager_v1":
        return generate_one_pager(out_path, scan_meta, vm)
    raise ValueError(f"Template PDF non supportato: {template}")


def generate_scan_pdf(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    return generate_report(out_path, scan_meta, vm, template="saas_scan_v1")


def generate_scan_pdf_enterprise(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = _build_context(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_scan_pages(c, ctx)
    c.save()
    return out_path


def generate_one_pager(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = _build_context(scan_meta, vm)
    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    render_one_pager(c, ctx)
    c.save()
    return out_path