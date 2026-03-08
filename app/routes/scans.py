from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from ..extensions import db
from ..models.scan import Scan
from ..services.pdf.engine import generate_one_pager, generate_scan_pdf_enterprise
from ..tenant import ensure_current_org_id

bp = Blueprint("scans", __name__)


def get_accessible_scan_or_404(scan_id: int) -> Scan:
    user = current_user._get_current_object()

    if getattr(user, "is_admin", False):
        return Scan.query.filter_by(id=scan_id).first_or_404()

    org_id = ensure_current_org_id()
    return Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()


@bp.get("/dashboard")
@login_required
def dashboard():
    org_id = ensure_current_org_id()

    scans = (
        Scan.query.filter_by(org_id=org_id)
        .order_by(Scan.id.desc())
        .all()
    )
    return render_template("dashboard.html", scans=scans)


@bp.get("/scan/<int:scan_id>")
@login_required
def view_scan(scan_id: int):
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
    vm.setdefault("action_plan", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})

    vm["state"].setdefault("overall", "GIALLO")
    vm["state"].setdefault("overall_score", 50)
    vm["state"].setdefault("confidenza", "MEDIA")
    vm["state"].setdefault("confidence", 50)
    vm["state"].setdefault("summary", "Report disponibile in modalità compatibile.")
    vm["state"].setdefault("risk_profile", "Profilo di rischio: Non disponibile")
    vm["state"].setdefault("maturity_label", "Maturità: Non disponibile")
    vm["state"].setdefault(
        "board_note",
        "Documento sintetico a supporto delle decisioni prioritarie del management.",
    )

    vm["risks"].setdefault("cash", 0.5)
    vm["risks"].setdefault("margini", 0.5)
    vm["risks"].setdefault("acq", 0.5)

    vm["decisions"].setdefault("cash", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("margini", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("acq", "Nessuna indicazione disponibile per questo report.")

    return render_template("scans/view_scan.html", scan=scan, vm=vm)


@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):
    scan = get_accessible_scan_or_404(scan_id)

    db.session.delete(scan)
    db.session.commit()

    flash(f"Scan #{scan_id} eliminato.")
    return redirect(url_for("scans.dashboard"))


@bp.post("/scans/bulk-delete", endpoint="bulk_delete")
@login_required
def bulk_delete():
    org_id = ensure_current_org_id()

    ids = request.form.getlist("scan_ids")
    if not ids:
        flash("Nessuna scansione selezionata.")
        return redirect(url_for("scans.dashboard"))

    clean_ids = []
    for item in ids:
        try:
            clean_ids.append(int(item))
        except Exception:
            pass

    if not clean_ids:
        flash("Nessuna scansione valida selezionata.")
        return redirect(url_for("scans.dashboard"))

    if getattr(current_user, "is_admin", False):
        q = Scan.query.filter(Scan.id.in_(clean_ids))
    else:
        q = Scan.query.filter(Scan.org_id == org_id, Scan.id.in_(clean_ids))

    n = q.count()
    q.delete(synchronize_session=False)
    db.session.commit()

    flash(f"Eliminate {n} scansioni.")
    return redirect(url_for("scans.dashboard"))


@bp.get("/scan/<int:scan_id>/pdf")
@login_required
def scan_pdf(scan_id: int):
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
    vm.setdefault("action_plan", triade.get("action_plan", []))
    vm.setdefault("alerts", triade.get("alerts", []))
    vm.setdefault("decisions", triade.get("decisions", {}))

    vm["state"].setdefault("overall", "GIALLO")
    vm["state"].setdefault("overall_score", 50)
    vm["state"].setdefault("confidenza", "MEDIA")
    vm["state"].setdefault("confidence", 50)
    vm["state"].setdefault("summary", "Report disponibile in modalità compatibile.")
    vm["state"].setdefault("risk_profile", "Profilo di rischio: Non disponibile")
    vm["state"].setdefault("maturity_label", "Maturità: Non disponibile")
    vm["state"].setdefault(
        "board_note",
        "Documento sintetico a supporto delle decisioni prioritarie del management.",
    )

    vm["risks"].setdefault("cash", 0.5)
    vm["risks"].setdefault("margini", 0.5)
    vm["risks"].setdefault("acq", 0.5)

    vm["decisions"].setdefault("cash", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("margini", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("acq", "Nessuna indicazione disponibile per questo report.")

    out_path = Path(current_app.instance_path) / f"scan_{scan.id}.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scan_meta = {
        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese_riferimento": scan.mese_riferimento,
        "created_at": str(scan.created_at)[:19].replace("T", " "),
    }

    generate_scan_pdf_enterprise(out_path, scan_meta, vm)

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SaaS_Full_Strategic_Report_{scan.id}.pdf",
    )


@bp.get("/scan/<int:scan_id>/onepager")
@login_required
def scan_onepager(scan_id: int):
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
    vm.setdefault("action_plan", triade.get("action_plan", []))
    vm.setdefault("alerts", triade.get("alerts", []))
    vm.setdefault("decisions", triade.get("decisions", {}))

    vm["state"].setdefault("overall", "GIALLO")
    vm["state"].setdefault("overall_score", 50)
    vm["state"].setdefault("confidenza", "MEDIA")
    vm["state"].setdefault("confidence", 50)
    vm["state"].setdefault("summary", "Report disponibile in modalità compatibile.")
    vm["state"].setdefault("risk_profile", "Profilo di rischio: Non disponibile")
    vm["state"].setdefault("maturity_label", "Maturità: Non disponibile")
    vm["state"].setdefault(
        "board_note",
        "Documento sintetico a supporto delle decisioni prioritarie del management.",
    )

    vm["risks"].setdefault("cash", 0.5)
    vm["risks"].setdefault("margini", 0.5)
    vm["risks"].setdefault("acq", 0.5)

    vm["decisions"].setdefault("cash", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("margini", "Nessuna indicazione disponibile per questo report.")
    vm["decisions"].setdefault("acq", "Nessuna indicazione disponibile per questo report.")

    out_path = Path(current_app.instance_path) / f"scan_{scan.id}_onepager.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scan_meta = {
        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese_riferimento": scan.mese_riferimento,
        "created_at": str(scan.created_at)[:19].replace("T", " "),
    }

    generate_one_pager(out_path, scan_meta, vm)

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SaaS_Full_Executive_OnePager_{scan.id}.pdf",
    )