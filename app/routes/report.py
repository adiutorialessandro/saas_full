from __future__ import annotations

import json
from typing import Any, Dict, List

from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from ..models.scan import Scan
from ..services.report_insights import report_header_payload
from ..tenant import ensure_current_org_id

bp = Blueprint("report", __name__, url_prefix="/report")


def get_accessible_scan_or_404(scan_id: int) -> Scan:
    user = current_user._get_current_object()

    if getattr(user, "is_admin", False):
        return Scan.query.filter_by(id=scan_id).first_or_404()

    org_id = ensure_current_org_id()
    return Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()


def safe_float(val: Any, default: float = 0.0) -> float:
    """Converte in modo sicuro in float, evitando i crash causati dai NoneType."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


@bp.get("/<int:scan_id>")
@login_required
def view_report(scan_id: int):
    scan = get_accessible_scan_or_404(scan_id)

    report: Dict[str, Any] = {}
    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    # Estraiamo la triade dal JSON generato dal service
    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    vm = triade if isinstance(triade, dict) else {}

    # --- 1. INIZIALIZZAZIONE SICURA ---
    # Sostituisce i setdefault per evitare crash se il JSON contiene 'null'
    for key in ["meta", "state", "risks", "kpi", "decisions"]:
        if not isinstance(vm.get(key), dict):
            vm[key] = {}
            
    for key in ["indicators", "alerts", "action_plan", "plan_tasks"]:
        if not isinstance(vm.get(key), list):
            vm[key] = []

    # Default Meta
    vm["meta"]["settore"] = vm["meta"].get("settore") or getattr(scan, "settore", "Non specificato")
    if "benchmark_settore" not in vm["meta"]:
        vm["meta"]["benchmark_settore"] = None

    # Default State
    vm["state"]["overall"] = vm["state"].get("overall") or "GIALLO"
    vm["state"]["overall_score"] = vm["state"].get("overall_score") if vm["state"].get("overall_score") is not None else 50
    vm["state"]["summary"] = vm["state"].get("summary") or "Analisi completata."
    vm["state"]["confidence"] = vm["state"].get("confidence") or 50
    vm["state"]["maturity_label"] = vm["state"].get("maturity_label") or "Maturità in fase di calcolo"

    # Default Rischi
    for r_key in ["cash", "margini", "acq"]:
        if vm["risks"].get(r_key) is None:
            vm["risks"][r_key] = 0.5

    # Default KPI
    for kpi_key in ["runway_mesi", "break_even_ratio", "conversione", "margine_pct", "burn_cash_ratio", "incassi_mese"]:
        if kpi_key not in vm["kpi"]:
            vm["kpi"][kpi_key] = None

    scan_meta = {
        "id": scan.id,
        "settore": getattr(scan, "settore", ""),
        "modello": getattr(scan, "modello", ""),
        "mese": getattr(scan, "mese_riferimento", ""),
        "created_at": getattr(scan, "created_at", None),
    }

    # --- 2. GESTIONE STORICO (HISTORY) ---
    if getattr(current_user, "is_admin", False):
        scans = Scan.query.filter_by(org_id=scan.org_id).order_by(Scan.created_at.asc(), Scan.id.asc()).all()
    else:
        org_id = ensure_current_org_id()
        scans = Scan.query.filter_by(org_id=org_id).order_by(Scan.created_at.asc(), Scan.id.asc()).all()

    history: List[Dict[str, Any]] = []
    for s in scans:
        try:
            r = json.loads(s.report_json or "{}")
            t = r.get("triade", {}) if isinstance(r, dict) else {}
            st = t.get("state", {}) if isinstance(t, dict) else {}
            rk = t.get("risks", {}) if isinstance(t, dict) else {}

            # Lettura sicura dello score
            score = getattr(s, "triad_index", None)
            if score is None:
                score = st.get("overall_score", 50.0)
            score = safe_float(score, 50.0)

            history.append({
                "id": s.id,
                "label": getattr(s, "mese_riferimento", None) or f"Scan {s.id}",
                "overall_score": score,
                "cash": round(safe_float(rk.get("cash", 0.5)) * 100, 1),
                "margini": round(safe_float(rk.get("margini", 0.5)) * 100, 1),
                "acq": round(safe_float(rk.get("acq", 0.5)) * 100, 1),
            })
        except Exception:
            continue

    # --- 3. CALCOLO DELTA SICURO ---
    delta = {"score": None, "cash": None, "margini": None, "acq": None}

    if len(history) >= 2:
        curr, prev = history[-1], history[-2]
        try:
            delta["score"] = round(curr["overall_score"] - prev["overall_score"], 1)
            delta["cash"] = round(curr["cash"] - prev["cash"], 1)
            delta["margini"] = round(curr["margini"] - prev["margini"], 1)
            delta["acq"] = round(curr["acq"] - prev["acq"], 1)
        except Exception:
            # Se per qualche motivo i calcoli falliscono, delta rimane None evitando il crash
            pass

    # Generazione payload dinamico per l'header (titolo e sottotitolo report)
    header_payload = report_header_payload(vm, delta)

    return render_template(
        "report_full.html",
        scan=scan,
        scan_meta=scan_meta,
        vm=vm,
        history=history,
        delta=delta,
        header_payload=header_payload,
    )


@bp.get("/api/triad-trend")
@login_required
def triad_trend():
    if getattr(current_user, "is_admin", False):
        scans = Scan.query.order_by(Scan.created_at.asc(), Scan.id.asc()).all()
    else:
        org_id = ensure_current_org_id()
        scans = Scan.query.filter_by(org_id=org_id).order_by(Scan.created_at.asc(), Scan.id.asc()).all()

    labels, values, finance, sales, ops = [], [], [], [], []

    for s in scans:
        labels.append(getattr(s, "mese_riferimento", None) or f"Scan {s.id}")

        t_index = getattr(s, "triad_index", None)
        if t_index is not None:
            values.append(round(safe_float(t_index, 50.0), 1))
        else:
            try:
                r = json.loads(s.report_json or "{}")
                t = r.get("triade", {}) if isinstance(r, dict) else {}
                st = t.get("state", {}) if isinstance(t, dict) else {}
                values.append(round(safe_float(st.get("overall_score", 50.0)), 1))
            except Exception:
                values.append(50.0)

        f_score = getattr(s, "finance_score", None)
        s_score = getattr(s, "sales_score", None)
        o_score = getattr(s, "ops_score", None)

        finance.append(round(safe_float(f_score), 1) if f_score is not None else None)
        sales.append(round(safe_float(s_score), 1) if s_score is not None else None)
        ops.append(round(safe_float(o_score), 1) if o_score is not None else None)

    return jsonify({
        "labels": labels,
        "values": values,
        "finance": finance,
        "sales": sales,
        "ops": ops,
    })