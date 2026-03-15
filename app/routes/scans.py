from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    current_app,
)

from flask_login import login_required, current_user

from ..extensions import db
from ..models.scan import Scan
from ..services.pdf.engine import (
    generate_scan_pdf_enterprise,
    generate_one_pager,
)
from ..tenant import ensure_current_org_id
from ..utils.benchmarks import get_benchmark_analysis


# Blueprint
bp = Blueprint("scans", __name__)


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def get_accessible_scan_or_404(scan_id: int) -> Scan:
    """
    Restituisce la scan se accessibile all'utente e non eliminata logicamente (Soft Delete).
    Admin vede tutto, utente solo la propria organization.
    """
    user = current_user._get_current_object()

    if getattr(user, "is_admin", False):
        return Scan.query.filter_by(id=scan_id, is_deleted=False).first_or_404()

    org_id = ensure_current_org_id()

    return Scan.query.filter_by(
        id=scan_id,
        org_id=org_id,
        is_deleted=False
    ).first_or_404()


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@bp.get("/dashboard")
@login_required
def dashboard():
    org_id = ensure_current_org_id()

    scans = (
        Scan.query
        .filter_by(org_id=org_id, is_deleted=False)
        .order_by(Scan.id.desc())
        .limit(100)
        .all()
    )
    return render_template(
        "dashboard.html",
        scans=scans
    )


# ---------------------------------------------------------
# View scan
# ---------------------------------------------------------

@bp.get("/scan/<int:scan_id>")
@login_required
def view_scan(scan_id: int):

    scan = get_accessible_scan_or_404(scan_id)

    report: Dict[str, Any] = {}

    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {})
    vm = triade if isinstance(triade, dict) else {}

    # fallback sicurezza struttura
    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("action_plan", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})

    # --------------------------------
    # Benchmark
    # --------------------------------
    settore = scan.settore
    kpi_data = vm.get("kpi", {})

    try:
        analysis = get_benchmark_analysis(settore, kpi_data)

        if isinstance(analysis, dict):
            vm["benchmark_results"] = (
                analysis.get("results")
                or analysis.get("benchmarks")
                or {}
            )

            vm["benchmark_raw"] = (
                analysis.get("benchmark")
                or analysis.get("raw")
                or {}
            )
        else:
            vm["benchmark_results"] = {}
            vm["benchmark_raw"] = {}

    except Exception:
        vm["benchmark_results"] = {}
        vm["benchmark_raw"] = {}

    return render_template(
        "scans/view_scan.html",
        scan=scan,
        vm=vm
    )


# ---------------------------------------------------------
# Delete scan (Soft Delete)
# ---------------------------------------------------------

@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):

    scan = get_accessible_scan_or_404(scan_id)

    # Invece di distruggere il record, lo marchiamo come eliminato
    scan.is_deleted = True
    db.session.commit()

    flash(f"Analisi rimossa dalla dashboard.")

    return redirect(
        url_for("scans.dashboard")
    )


# ---------------------------------------------------------
# Bulk delete (Soft Delete)
# ---------------------------------------------------------

@bp.post("/scans/bulk-delete")
@login_required
def bulk_delete():

    org_id = ensure_current_org_id()

    ids = request.form.getlist("scan_ids")

    if not ids:
        flash("Nessuna scansione selezionata.")
        return redirect(url_for("scans.dashboard"))

    clean_ids = []

    for i in ids:
        try:
            clean_ids.append(int(i))
        except Exception:
            pass

    if not clean_ids:
        flash("Nessuna scansione valida.")
        return redirect(url_for("scans.dashboard"))

    if getattr(current_user, "is_admin", False):
        q = Scan.query.filter(Scan.id.in_(clean_ids))
    else:
        q = Scan.query.filter(
            Scan.org_id == org_id,
            Scan.id.in_(clean_ids)
        )

    deleted = q.count()

    # Eseguiamo un update di massa invece di una delete
    q.update({"is_deleted": True}, synchronize_session=False)

    db.session.commit()

    flash(f"Rimosse {deleted} analisi dalla dashboard.")

    return redirect(
        url_for("scans.dashboard")
    )


# ---------------------------------------------------------
# PDF completo
# ---------------------------------------------------------

@bp.get("/scan/<int:scan_id>/pdf")
@login_required
def scan_pdf(scan_id: int):

    scan = get_accessible_scan_or_404(scan_id)

    report: Dict[str, Any] = {}

    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {})
    vm = triade if isinstance(triade, dict) else {}

    # sicurezza struttura dati
    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("action_plan", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})

    settore = scan.settore
    kpi_data = vm.get("kpi", {})

    try:
        analysis = get_benchmark_analysis(settore, kpi_data)

        if isinstance(analysis, dict):
            vm["benchmark_results"] = (
                analysis.get("results")
                or analysis.get("benchmarks")
                or {}
            )

            vm["benchmark_raw"] = (
                analysis.get("benchmark")
                or analysis.get("raw")
                or {}
            )
        else:
            vm["benchmark_results"] = {}
            vm["benchmark_raw"] = {}

    except Exception:
        vm["benchmark_results"] = {}
        vm["benchmark_raw"] = {}

    out_path = (
        Path(current_app.instance_path)
        / f"scan_{scan.id}.pdf"
    )

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # forza rigenerazione pdf (evita cache vecchie versioni)
    if out_path.exists():
        try:
            out_path.unlink()
        except Exception:
            pass

    scan_meta = {

        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese_riferimento": scan.mese_riferimento,
        "created_at": str(scan.created_at)[:19].replace("T", " "),

    }

    generate_scan_pdf_enterprise(
        out_path,
        scan_meta,
        vm
    )

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Triad_Insight_Report_Salone_{scan.id}.pdf",
    )


# ---------------------------------------------------------
# One pager
# ---------------------------------------------------------

@bp.get("/scan/<int:scan_id>/onepager")
@login_required
def scan_onepager(scan_id: int):

    scan = get_accessible_scan_or_404(scan_id)

    report: Dict[str, Any] = {}

    try:
        report = json.loads(scan.report_json or "{}")
    except Exception:
        report = {}

    triade = report.get("triade", {})
    vm = triade if isinstance(triade, dict) else {}

    # sicurezza struttura dati
    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("action_plan", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})

    settore = scan.settore
    kpi_data = vm.get("kpi", {})

    try:
        analysis = get_benchmark_analysis(settore, kpi_data)

        if isinstance(analysis, dict):
            vm["benchmark_results"] = (
                analysis.get("results")
                or analysis.get("benchmarks")
                or {}
            )

            vm["benchmark_raw"] = (
                analysis.get("benchmark")
                or analysis.get("raw")
                or {}
            )
        else:
            vm["benchmark_results"] = {}
            vm["benchmark_raw"] = {}

    except Exception:
        vm["benchmark_results"] = {}
        vm["benchmark_raw"] = {}

    out_path = (
        Path(current_app.instance_path)
        / f"scan_{scan.id}_onepager.pdf"
    )

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # forza rigenerazione pdf (evita cache vecchie versioni)
    if out_path.exists():
        try:
            out_path.unlink()
        except Exception:
            pass

    scan_meta = {

        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese_riferimento": scan.mese_riferimento,
        "created_at": str(scan.created_at)[:19].replace("T", " "),

    }

    generate_one_pager(
        out_path,
        scan_meta,
        vm
    )

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Triad_Insight_Executive_OnePager_{scan.id}.pdf",
    )