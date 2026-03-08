from __future__ import annotations

import json
from typing import Any, Dict, List

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..models.scan import Scan
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

    # storico
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

            history.append(
                {
                    "id": s.id,
                    "label": s.mese_riferimento or f"Scan {s.id}",
                    "overall_score": state.get("overall_score", 50),
                    "cash": round(float(risks.get("cash", 0.5)) * 100, 1),
                    "margini": round(float(risks.get("margini", 0.5)) * 100, 1),
                    "acq": round(float(risks.get("acq", 0.5)) * 100, 1),
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

    return render_template(
        "report_full.html",
        scan=scan,
        scan_meta=scan_meta,
        vm=vm,
        history=history,
        delta=delta,
    )