import json
from pathlib import Path

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
from flask_login import login_required

from ..extensions import db
from ..models.scan import Scan
from ..tenant import ensure_current_org_id
from app.services.pdf.engine import generate_scan_pdf_enterprise

bp = Blueprint("scans", __name__)


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
    org_id = ensure_current_org_id()
    scan = Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()

    report = {}
    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    vm = triade if isinstance(triade, dict) else {}

    # safety defaults
    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("action_plan", [])
    vm.setdefault("alerts", [])

    return render_template("scans/view_scan.html", scan=scan, vm=vm)


@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):
    org_id = ensure_current_org_id()
    scan = Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()

    db.session.delete(scan)
    db.session.commit()

    flash(f"Scan #{scan_id} eliminato.")
    return redirect(url_for("scans.dashboard"))


@bp.post("/scans/bulk-delete", endpoint="bulk_delete")
@login_required
def bulk_delete():
    """
    Bulk delete stile “mail”: riceve scan_ids[] dal form.
    Endpoint stabile: scans.bulk_delete
    """
    org_id = ensure_current_org_id()

    ids = request.form.getlist("scan_ids")
    if not ids:
        flash("Nessuna scansione selezionata.")
        return redirect(url_for("scans.dashboard"))

    clean_ids = []
    for x in ids:
        try:
            clean_ids.append(int(x))
        except Exception:
            continue

    if not clean_ids:
        flash("Selezione non valida.")
        return redirect(url_for("scans.dashboard"))

    q = Scan.query.filter(Scan.org_id == org_id, Scan.id.in_(clean_ids))
    n = q.count()
    q.delete(synchronize_session=False)
    db.session.commit()

    flash(f"Eliminate {n} scansioni.")
    return redirect(url_for("scans.dashboard"))


@bp.get("/scan/<int:scan_id>/pdf")
@login_required
def scan_pdf(scan_id: int):
    org_id = ensure_current_org_id()
    scan = Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()

    report = {}
    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    triade = triade if isinstance(triade, dict) else {}

    # VM safe for PDF
    vm = dict(triade)
    vm.setdefault("state", triade.get("state", {}))
    vm.setdefault("risks", triade.get("risks", {}))
    vm.setdefault("kpi", triade.get("kpi", {}))
    vm.setdefault("indicators", triade.get("indicators", []))
    vm.setdefault("action_plan", triade.get("action_plan", []))
    vm.setdefault("alerts", triade.get("alerts", []))

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
        as_attachment=True,
        download_name=f"Saas_full_scan_{scan.id}.pdf",
        mimetype="application/pdf",
    )
