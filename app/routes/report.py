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


@bp.get("/<int:scan_id>")
@login_required
def view_report(scan_id: int):
    scan = get_accessible_scan_or_404(scan_id)

    report: Dict[str, Any] = {}
    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    vm = triade if isinstance(triade, dict) else {}

    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})
    vm.setdefault("action_plan", [])
    vm.setdefault("plan_tasks", [])

    vm["state"].setdefault("overall", "GIALLO")
    vm["state"].setdefault("overall_score", 50)
    vm["state"].setdefault("summary", "Report disponibile.")
    vm["state"].setdefault("confidence", 50)
    vm["state"].setdefault("risk_profile", "Profilo di rischio")
    vm["state"].setdefault("maturity_label", "Maturità non disponibile")

    vm["risks"].setdefault("cash", 0.5)
    vm["risks"].setdefault("margini", 0.5)
    vm["risks"].setdefault("acq", 0.5)

    vm["kpi"].setdefault("runway_mesi", None)
    vm["kpi"].setdefault("break_even_ratio", None)
    vm["kpi"].setdefault("conversione", None)
    vm["kpi"].setdefault("margine_pct", None)
    vm["kpi"].setdefault("burn_cash_ratio", None)
    vm["kpi"].setdefault("incassi_mese", None)

    scan_meta = {
        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese": scan.mese_riferimento,
        "created_at": scan.created_at,
    }

    if getattr(current_user, "is_admin", False):
        scans = (
            Scan.query.filter_by(org_id=scan.org_id)
            .order_by(Scan.created_at.asc(), Scan.id.asc())
            .all()
        )
    else:
        org_id = ensure_current_org_id()
        scans = (
            Scan.query.filter_by(org_id=org_id)
            .order_by(Scan.created_at.asc(), Scan.id.asc())
            .all()
        )

    history: List[Dict[str, Any]] = []
    for s in scans:
        try:
            r = json.loads(s.report_json or "{}")
            t = r.get("triade", {}) if isinstance(r, dict) else {}
            state = t.get("state", {}) if isinstance(t, dict) else {}
            risks = t.get("risks", {}) if isinstance(t, dict) else {}

            overall_score = s.triad_index if s.triad_index is not None else state.get("overall_score", 50)

            history.append(
                {
                    "id": s.id,
                    "label": s.mese_riferimento or f"Scan {s.id}",
                    "overall_score": overall_score,
                    "cash": round(float(risks.get("cash", 0.5)) * 100, 1),
                    "margini": round(float(risks.get("margini", 0.5)) * 100, 1),
                    "acq": round(float(risks.get("acq", 0.5)) * 100, 1),
                    "finance_score": round(float(s.finance_score), 1) if s.finance_score is not None else None,
                    "sales_score": round(float(s.sales_score), 1) if s.sales_score is not None else None,
                    "ops_score": round(float(s.ops_score), 1) if s.ops_score is not None else None,
                }
            )
        except Exception:
            history.append(
                {
                    "id": s.id,
                    "label": s.mese_riferimento or f"Scan {s.id}",
                    "overall_score": 50,
                    "cash": 50.0,
                    "margini": 50.0,
                    "acq": 50.0,
                    "finance_score": None,
                    "sales_score": None,
                    "ops_score": None,
                }
            )

    delta = {
        "score": None,
        "cash": None,
        "margini": None,
        "acq": None,
    }

    if len(history) >= 2:
        current = history[-1]
        previous = history[-2]

        try:
            delta["score"] = round(float(current["overall_score"]) - float(previous["overall_score"]), 1)
        except Exception:
            delta["score"] = None

        try:
            delta["cash"] = round(float(current["cash"]) - float(previous["cash"]), 1)
        except Exception:
            delta["cash"] = None

        try:
            delta["margini"] = round(float(current["margini"]) - float(previous["margini"]), 1)
        except Exception:
            delta["margini"] = None

        try:
            delta["acq"] = round(float(current["acq"]) - float(previous["acq"]), 1)
        except Exception:
            delta["acq"] = None

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
        scans = (
            Scan.query.order_by(Scan.created_at.asc(), Scan.id.asc()).all()
        )
    else:
        org_id = ensure_current_org_id()
        scans = (
            Scan.query.filter_by(org_id=org_id)
            .order_by(Scan.created_at.asc(), Scan.id.asc())
            .all()
        )

    labels: List[str] = []
    values: List[float] = []
    finance: List[float | None] = []
    sales: List[float | None] = []
    ops: List[float | None] = []

    for s in scans:
        labels.append(s.mese_riferimento or f"Scan {s.id}")

        if s.triad_index is not None:
            values.append(round(float(s.triad_index), 1))
        else:
            try:
                report = json.loads(s.report_json or "{}")
                triade = report.get("triade", {}) if isinstance(report, dict) else {}
                state = triade.get("state", {}) if isinstance(triade, dict) else {}
                values.append(round(float(state.get("overall_score", 50)), 1))
            except Exception:
                values.append(50.0)

        finance.append(round(float(s.finance_score), 1) if s.finance_score is not None else None)
        sales.append(round(float(s.sales_score), 1) if s.sales_score is not None else None)
        ops.append(round(float(s.ops_score), 1) if s.ops_score is not None else None)

    return jsonify(
        {
            "labels": labels,
            "values": values,
            "finance": finance,
            "sales": sales,
            "ops": ops,
        }
    )