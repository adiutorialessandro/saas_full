from __future__ import annotations

import json
from typing import Any, Dict

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

    return render_template(
        "reports/report_full.html",
        scan=scan,
        scan_meta=scan_meta,
        vm=vm,
    )