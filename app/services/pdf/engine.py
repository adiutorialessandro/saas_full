from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.pdfgen import canvas

from .config import PAGE_SIZE
from .pages import render_scan_pages, render_one_pager
from .utils import clamp01
from .narrative import (
    hero_insight,
    drivers_payload,
    benchmark_meta_payload,
    plan_tasks_payload,
    confidence_score,
)


def _risk_label(v: float | None) -> str:
    v = clamp01(v, 0.5)

    if v >= 0.66:
        return "ROSSO"

    if v >= 0.33:
        return "GIALLO"

    return "VERDE"


def _triad_index(vm: Dict[str, Any]) -> float:
    risks = vm.get("risks") or {}

    cash = clamp01(risks.get("cash"), 0.5)
    marg = clamp01(risks.get("margini"), 0.5)
    acq = clamp01(risks.get("acq"), 0.5)

    avg_risk = (cash + marg + acq) / 3

    triad = (1 - avg_risk) * 100

    return max(0, min(100, triad))


def _build_ctx(scan_meta: Dict[str, Any], vm: Dict[str, Any]) -> Dict[str, Any]:
    risks = vm.get("risks") or {}
    kpi = vm.get("kpi") or {}
    indicators = vm.get("indicators") or []

    cash_r = clamp01(risks.get("cash"), 0.5)
    marg_r = clamp01(risks.get("margini"), 0.5)
    acq_r = clamp01(risks.get("acq"), 0.5)

    triad = _triad_index(vm)

    risk_profile = max(
        [
            ("CASSA", cash_r),
            ("MARGINI", marg_r),
            ("ACQUISIZIONE", acq_r),
        ],
        key=lambda x: x[1],
    )[0]

    overall = _risk_label(max(cash_r, marg_r, acq_r))

    ctx = {
        "settore": scan_meta.get("settore") or "Settore",
        "modello": scan_meta.get("modello") or "Business model",
        "mese": scan_meta.get("mese_riferimento") or "Periodo",
        "overall": overall,
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
    }

    return ctx


def generate_scan_pdf_enterprise(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    """
    Genera il report completo enterprise (5 pagine)
    """

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
    """
    Alias compatibilità
    """

    return generate_scan_pdf_enterprise(out_path, scan_meta, vm)


def generate_report(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    """
    Alias legacy
    """

    return generate_scan_pdf_enterprise(out_path, scan_meta, vm)


def generate_onepager_pdf(
    out_path: str | Path,
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    """
    Genera versione onepager executive
    """

    out_path = Path(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = _build_ctx(scan_meta, vm)

    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)

    render_one_pager(c, ctx)

    c.save()

    return out_path