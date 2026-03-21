"""
SaaS Full - Scans & Reports Controller
Gestisce la visualizzazione delle dashboard, l'esportazione PDF e l'eliminazione dei report.
Implementa controlli di sicurezza multi-tenant e logiche DRY per il caricamento dei dati.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
)
from flask_login import login_required, current_user

from ..extensions import db
from ..models.scan import Scan
from ..services.pdf.engine import generate_scan_pdf_enterprise, generate_one_pager
from ..tenant import ensure_current_org_id
from ..utils.benchmarks import get_benchmark_analysis

# Configurazione Logger per tracciabilità
logger = logging.getLogger(__name__)

bp = Blueprint("scans", __name__)


# =========================================================
# CORE UTILITIES (Private Methods)
# =========================================================

def _get_accessible_scan_or_404(scan_id: int) -> Scan:
    """
    Recupera uno scan garantendo l'isolamento tenant (Multi-Tenancy).
    Gli amministratori bypassano il filtro org_id.
    """
    user = current_user._get_current_object()
    
    if getattr(user, "is_admin", False):
        return Scan.query.filter_by(id=scan_id).first_or_404()

    org_id = ensure_current_org_id()
    return Scan.query.filter_by(id=scan_id, org_id=org_id).first_or_404()


def _prepare_scan_view_model(scan: Scan) -> Dict[str, Any]:
    """
    [DRY] Funzione centralizzata per il parsing del report JSON e l'arricchimento
    con i benchmark. Evita la duplicazione della logica nelle varie route.
    """
    try:
        report = json.loads(scan.report_json or "{}")
    except json.JSONDecodeError as e:
        logger.error(f"Errore parsing JSON per Scan ID {scan.id}: {str(e)}")
        report = {}

    triade = report.get("triade", {})
    vm = triade if isinstance(triade, dict) else {}

    # Fallback strutturali per garantire la stabilità del frontend Jinja2
    defaults = {
        "meta": {}, "state": {}, "risks": {}, "kpi": {}, 
        "decisions": {}, "action_plan": [], "advanced_strategy": {}
    }
    for key, default_val in defaults.items():
        vm.setdefault(key, default_val)

    # Arricchimento Benchmark Dinamici
    try:
        analysis = get_benchmark_analysis(scan.settore, vm["kpi"])
        if isinstance(analysis, dict):
            vm["benchmark_results"] = analysis.get("results") or analysis.get("benchmarks") or {}
            vm["benchmark_raw"] = analysis.get("benchmark") or analysis.get("raw") or {}
        else:
            vm["benchmark_results"] = {}
            vm["benchmark_raw"] = {}
    except Exception as e:
        logger.error(f"Errore recupero benchmark per Scan ID {scan.id}: {str(e)}")
        vm["benchmark_results"] = {}
        vm["benchmark_raw"] = {}

    return vm


def _get_scan_meta(scan: Scan) -> Dict[str, Any]:
    """Genera i metadati essenziali standardizzati per le intestazioni PDF."""
    return {
        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese_riferimento": scan.mese_riferimento,
        "created_at": scan.created_at.strftime("%Y-%m-%d %H:%M:%S") if scan.created_at else "N/A",
    }


# =========================================================
# WEB ROUTES
# =========================================================

@bp.get("/dashboard")
@login_required
def dashboard():
    """Mostra lo storico degli scan dell'organizzazione corrente."""
    org_id = ensure_current_org_id()
    scans = Scan.query.filter_by(org_id=org_id).order_by(Scan.id.desc()).all()
    
    return render_template("dashboard.html", scans=scans)


@bp.get("/scan/<int:scan_id>")
@login_required
def view_scan(scan_id: int):
    """Renderizza la dashboard HTML interattiva dello scan."""
    scan = _get_accessible_scan_or_404(scan_id)
    vm = _prepare_scan_view_model(scan)
    
    return render_template("scans/view_scan.html", scan=scan, vm=vm)


# =========================================================
# DELETION LOGIC
# =========================================================

@bp.post("/scan/<int:scan_id>/delete")
@login_required
def delete_scan(scan_id: int):
    """Elimina una singola scansione in sicurezza."""
    scan = _get_accessible_scan_or_404(scan_id)
    
    db.session.delete(scan)
    db.session.commit()
    logger.info(f"Scan ID {scan_id} eliminato dall'utente {current_user.email}")
    flash(f"Scan #{scan_id} eliminato con successo.", "success")
    
    return redirect(url_for("scans.dashboard"))


@bp.post("/scans/bulk-delete")
@login_required
def bulk_delete():
    """Elimina scansioni multiple selezionate dalla dashboard."""
    raw_ids = request.form.getlist("scan_ids")

    if not raw_ids:
        flash("Nessuna scansione selezionata.", "warning")
        return redirect(url_for("scans.dashboard"))

    # Pulizia input (protezione injection)
    clean_ids = [int(i) for i in raw_ids if i.isdigit()]

    if not clean_ids:
        flash("ID scansioni non validi.", "danger")
        return redirect(url_for("scans.dashboard"))

    q = Scan.query.filter(Scan.id.in_(clean_ids))
    
    # FIX: Evitiamo che ensure_current_org_id() crashi se chiamato da un Admin
    if not getattr(current_user, "is_admin", False):
        org_id = ensure_current_org_id()
        q = q.filter(Scan.org_id == org_id)

    deleted_count = q.delete(synchronize_session=False)
    db.session.commit()

    logger.info(f"Bulk delete: rimossi {deleted_count} scan dall'utente {current_user.email}")
    flash(f"Eliminate {deleted_count} scansioni con successo.", "success")
    
    return redirect(url_for("scans.dashboard"))


# =========================================================
# PDF EXPORT ROUTES
# =========================================================

@bp.get("/scan/<int:scan_id>/pdf")
@login_required
def scan_pdf(scan_id: int):
    """Genera e scarica il report strategico completo in formato PDF."""
    scan = _get_accessible_scan_or_404(scan_id)
    vm = _prepare_scan_view_model(scan)
    scan_meta = _get_scan_meta(scan)

    # FIX: Aggiunto UUID per prevenire la sovrascrittura di file in caso di richieste simultanee
    unique_suffix = uuid.uuid4().hex[:8]
    out_path = Path(current_app.instance_path) / f"scan_report_{scan.id}_{unique_suffix}.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Convertito in stringa per massima compatibilità con la libreria PDF
    generate_scan_pdf_enterprise(str(out_path), scan_meta, vm)

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SaaS_Full_Strategic_Report_{scan.id}.pdf",
    )


@bp.get("/scan/<int:scan_id>/onepager")
@login_required
def scan_onepager(scan_id: int):
    """Genera e scarica l'Executive Summary (One Pager) in formato PDF."""
    scan = _get_accessible_scan_or_404(scan_id)
    vm = _prepare_scan_view_model(scan)
    scan_meta = _get_scan_meta(scan)

    # FIX: Aggiunto UUID anche qui
    unique_suffix = uuid.uuid4().hex[:8]
    out_path = Path(current_app.instance_path) / f"scan_executive_{scan.id}_{unique_suffix}.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    generate_one_pager(str(out_path), scan_meta, vm)

    return send_file(
        out_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SaaS_Full_Executive_Summary_{scan.id}.pdf",
    )