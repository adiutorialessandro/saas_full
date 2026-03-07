from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import math

from reportlab.lib import colors
from reportlab.pdfgen import canvas

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

from .config import (
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    DEFAULT_TOTAL_PAGES,
    PAGE_SIZE,
    SECTOR_BENCHMARKS,
)
from app.services.analysis.simulator import scenario_matrix
from app.services.analysis.stress_test import stress_cashflow
from app.services.analysis.decision_engine import strategic_actions

from .narrative import (
    plan_tasks_payload,
    benchmark_meta_payload,
    drivers_payload,
    hero_insight,
    confidence_score,
    data_quality,
    definitions_payload,
    drivers_engine,
    benchmark_meta,
    plan_tasks,
)
from .pages import (
    _page_1_executive,
    _page_2_risk_snapshot,
    _page_3_kpi,
    _page_4_radar,
    _page_5_execution,
    _one_pager_executive,  # template 1 pagina
)

from .utils import clamp01, now_str, triad_index

# ---------------------------------------------------------
# Executive Resilience Score (ERS)
# sintetizza resilienza aziendale su scala 0–100
# ---------------------------------------------------------
def executive_resilience_score(ctx: Dict[str, Any]) -> float:
    triad = ctx.get("triad", 50) or 50
    confidence = ctx.get("confidence", 50) or 50

    cash_r = ctx.get("cash_r", 0.5) or 0.5
    marg = ctx.get("marg", 0) or 0
    conv = ctx.get("conv", 0) or 0

    try:
        if marg > 1:
            marg = marg / 100.0
        if conv > 1:
            conv = conv / 100.0
    except Exception:
        marg = 0
        conv = 0

    score = (
        0.40 * float(triad) +
        0.20 * float(confidence) +
        0.20 * (1 - float(cash_r)) * 100 +
        0.10 * float(marg) * 100 +
        0.10 * float(conv) * 100
    )

    return round(score, 1)


# =========================================================
# Helpers
# =========================================================
def _as_color(value: Any, default: colors.Color) -> colors.Color:
    if isinstance(value, colors.Color):
        return value
    if isinstance(value, str):
        try:
            return colors.HexColor(value)
        except Exception:
            return default
    return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _generate_triade_radar_chart(risks: Dict[str, Any], out_path: Path) -> Optional[Path]:
    if plt is None:
        return None

    labels = ["Cash", "Margins", "Acquisition"]
    values = [
        clamp01(risks.get("cash"), 0.5) or 0.5,
        clamp01(risks.get("margini"), 0.5) or 0.5,
        clamp01(risks.get("acq"), 0.5) or 0.5,
    ]

    values = values + values[:1]
    angles = [n / float(len(labels)) * 2.0 * math.pi for n in range(len(labels))]
    angles += angles[:1]

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(4.4, 4.0))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.20)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(["25", "50", "75", "100"])
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return out_path


def _generate_risk_bar_chart(risks: Dict[str, Any], out_path: Path) -> Optional[Path]:
    if plt is None:
        return None

    labels = ["Cash", "Margins", "Acquisition"]
    values = [
        (clamp01(risks.get("cash"), 0.5) or 0.5) * 100,
        (clamp01(risks.get("margini"), 0.5) or 0.5) * 100,
        (clamp01(risks.get("acq"), 0.5) or 0.5) * 100,
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(5.2, 3.2))
    ax = fig.add_subplot(111)
    bars = ax.bar(labels, values)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Risk Score")
    ax.set_title("Business Risk Profile")
    ax.grid(axis="y", alpha=0.20)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val:.0f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return out_path


def _build_chart_assets(asset_dir: Optional[Path], vm: Dict[str, Any]) -> Dict[str, Optional[str]]:
    if asset_dir is None:
        return {
            "triade_radar_chart": None,
            "risk_bar_chart": None,
        }

    risks = vm.get("risks") or {}
    radar_path = _generate_triade_radar_chart(risks, asset_dir / "triade_radar.png")
    bar_path = _generate_risk_bar_chart(risks, asset_dir / "risk_profile.png")

    return {
        "triade_radar_chart": str(radar_path) if radar_path else None,
        "risk_bar_chart": str(bar_path) if bar_path else None,
    }


def _build_context(scan_meta: Dict[str, Any], vm: Dict[str, Any], asset_dir: Optional[Path] = None) -> Dict[str, Any]:
    branding = vm.get("branding") or {}
    primary = _as_color(branding.get("primary"), DEFAULT_PRIMARY)
    accent = _as_color(branding.get("accent"), DEFAULT_ACCENT)
    watermark_text = str(branding.get("watermark", "CONFIDENTIAL") or "CONFIDENTIAL")
    logo_path = branding.get("logo_path")

    risks = vm.get("risks") or {}
    state = vm.get("state") or {}
    kpi = vm.get("kpi") or {}

    settore = scan_meta.get("settore", "—")
    modello = scan_meta.get("modello", "—")
    mese = scan_meta.get("mese_riferimento", "—")
    created_at = scan_meta.get("created_at") or now_str()
    scan_id = scan_meta.get("id", "—")

    overall = (state.get("overall") or state.get("stato") or "STABILE")
    overall = str(overall).upper()
    if overall in ("ROSSO", "GIALLO", "VERDE"):
        overall = {"ROSSO": "CRITICO", "GIALLO": "ATTENZIONE", "VERDE": "STABILE"}[overall]

    triad = triad_index(risks)
    confidence = confidence_score(vm)

    sector_key = settore if settore in SECTOR_BENCHMARKS else "Default"
    benchmark = SECTOR_BENCHMARKS.get(sector_key, SECTOR_BENCHMARKS["Default"])

    cash_r = clamp01(risks.get("cash"), 0.5) or 0.5
    marg_r = clamp01(risks.get("margini"), 0.5) or 0.5
    acq_r = clamp01(risks.get("acq"), 0.5) or 0.5

    hero = hero_insight(vm)
    dq = data_quality(vm, scan_meta)
    defs = definitions_payload(vm)
    drivers = drivers_engine(vm, scan_meta)
    bm = benchmark_meta(vm, settore)
    plan = plan_tasks(vm, kpi)
    chart_assets = _build_chart_assets(asset_dir, vm)

    ctx = {
        "schema_version": "1.2",
        "scenarios": scenario_matrix(vm.get("kpi", {})),
        "stress_test": stress_cashflow(vm.get("kpi", {})),
        "actions": strategic_actions(vm.get("kpi", {})),
        # input refs
        "vm": vm,
        "scan_meta": scan_meta,

        # branding
        "primary": primary,
        "accent": accent,
        "watermark_text": watermark_text,
        "logo_path": logo_path,

        # header/meta
        "settore": settore,
        "modello": modello,
        "mese": mese,
        "created_at": created_at,
        "scan_id": scan_id,
        "overall": overall,

        # scores
        "triad": triad,
        "confidence": confidence,
        "dq": dq,

        # risks for cards/radar
        "cash_r": cash_r,
        "marg_r": marg_r,
        "acq_r": acq_r,
        "benchmark": benchmark,
        "benchmark_meta": bm,  # v1.2
        "bm": bm,              # alias compat

        # narrative blocks
        "hero": hero,
        "defs": defs,
        "drivers": drivers,
        "plan": plan,

        # generated chart assets for premium PDF pages
        "triade_radar_chart": chart_assets.get("triade_radar_chart"),
        "risk_bar_chart": chart_assets.get("risk_bar_chart"),

        # KPIs commonly used
        "runway": kpi.get("runway_mesi"),
        "be": kpi.get("break_even_ratio"),
        "conv": kpi.get("conversione"),
        "marg": kpi.get("margine_pct"),
        "ncf": kpi.get("net_cash_flow"),
        "be_rev": kpi.get("break_even_ricavi"),
    }

    # Backward-compatible aliases (single source of truth: narrative.py v1.2)
    ctx["definitions"] = defs
    ctx["drivers"] = drivers
    ctx["benchmark_meta"] = bm
    ctx["plan_tasks"] = plan

    ctx["ers"] = executive_resilience_score(ctx)
    return ctx
# =========================================================
# PUBLIC API
# =========================================================
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
    raise ValueError(f"Unknown template: {template}")


# Backward compatible alias
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

    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    scan_id = scan_meta.get("id", "report")
    asset_dir = out_path.parent / "_assets" / f"scan_{scan_id}"
    ctx = _build_context(scan_meta, vm, asset_dir=asset_dir)

    total_pages = DEFAULT_TOTAL_PAGES

    # DEV mode: render a single page quickly
    render_only = vm.get("render_only_page") or vm.get("dev_page")
    if isinstance(render_only, int) and 1 <= render_only <= total_pages:
        right = f"DEV: pagina {render_only}/{total_pages}"
        if render_only == 1:
            _page_1_executive(c, ctx, 1, 1, right_label=right)
        elif render_only == 2:
            _page_2_risk_snapshot(c, ctx, 1, 1, right_label=right)
        elif render_only == 3:
            _page_3_kpi(c, ctx, 1, 1, right_label=right)
        elif render_only == 4:
            _page_4_radar(c, ctx, 1, 1, right_label=right)
        else:
            _page_5_execution(c, ctx, 1, 1, right_label=right)
        c.save()
        return out_path

    _page_1_executive(c, ctx, 1, total_pages)
    c.showPage()

    _page_2_risk_snapshot(c, ctx, 2, total_pages)
    c.showPage()

    _page_3_kpi(c, ctx, 3, total_pages)
    c.showPage()

    _page_4_radar(c, ctx, 4, total_pages)
    c.showPage()

    _page_5_execution(c, ctx, 5, total_pages)

    c.save()
    return out_path


def generate_one_pager(
    out_path: Union[str, Path],
    scan_meta: Dict[str, Any],
    vm: Dict[str, Any],
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=PAGE_SIZE)
    scan_id = scan_meta.get("id", "report")
    asset_dir = out_path.parent / "_assets" / f"scan_{scan_id}"
    ctx = _build_context(scan_meta, vm, asset_dir=asset_dir)

    _one_pager_executive(c, ctx, 1, 1)
    c.save()
    return out_path
