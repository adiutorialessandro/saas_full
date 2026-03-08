from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.services.pdf.engine import (
    generate_scan_pdf_enterprise,
    generate_one_pager,
)

bp = Blueprint("scans", __name__, url_prefix="/scans")


# =====================================================
# Helper
# =====================================================

def _load_scan(scan_id: str) -> Dict[str, Any]:
    """
    Carica i dati di uno scan dal filesystem.
    """
    data_dir = Path(current_app.config.get("SCAN_STORAGE", "instance/scans"))
    scan_file = data_dir / f"{scan_id}.json"

    if not scan_file.exists():
        raise FileNotFoundError(f"Scan {scan_id} non trovato")

    with open(scan_file) as f:
        return json.load(f)


def _output_dir() -> Path:
    """
    Directory output PDF
    """
    out = Path(current_app.config.get("PDF_OUTPUT_DIR", "instance/reports"))
    out.mkdir(parents=True, exist_ok=True)
    return out


# =====================================================
# Dashboard scans
# =====================================================

@bp.route("/")
def dashboard():
    """
    Elenco scans salvati
    """

    data_dir = Path(current_app.config.get("SCAN_STORAGE", "instance/scans"))
    scans = []

    if data_dir.exists():
        for f in sorted(data_dir.glob("*.json")):
            try:
                with open(f) as fh:
                    scans.append(json.load(fh))
            except Exception:
                pass

    return render_template(
        "scans/dashboard.html",
        scans=scans,
        title="SaaS Full — Business Scans",
    )


# =====================================================
# Visualizzazione scan
# =====================================================

@bp.route("/<scan_id>")
def view_scan(scan_id: str):

    scan = _load_scan(scan_id)

    return render_template(
        "scans/view.html",
        scan=scan,
        title=f"SaaS Full — Scan {scan_id}",
    )


# =====================================================
# Download PDF completo
# =====================================================

@bp.route("/<scan_id>/report")
def download_report(scan_id: str):

    scan = _load_scan(scan_id)

    scan_meta = scan.get("meta", {})
    vm = scan.get("vm", {})

    out_dir = _output_dir()

    pdf_path = out_dir / f"saas_full_scan_{scan_id}.pdf"

    generate_scan_pdf_enterprise(
        pdf_path,
        scan_meta,
        vm,
    )

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"SaaS_Full_Strategic_Report_{scan_id}.pdf",
        mimetype="application/pdf",
    )


# =====================================================
# Download One Pager
# =====================================================

@bp.route("/<scan_id>/onepager")
def download_onepager(scan_id: str):

    scan = _load_scan(scan_id)

    scan_meta = scan.get("meta", {})
    vm = scan.get("vm", {})

    out_dir = _output_dir()

    pdf_path = out_dir / f"saas_full_onepager_{scan_id}.pdf"

    generate_one_pager(
        pdf_path,
        scan_meta,
        vm,
    )

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"SaaS_Full_Executive_OnePager_{scan_id}.pdf",
        mimetype="application/pdf",
    )


# =====================================================
# Generazione + redirect
# =====================================================

@bp.route("/<scan_id>/generate")
def generate_and_open(scan_id: str):

    scan = _load_scan(scan_id)

    scan_meta = scan.get("meta", {})
    vm = scan.get("vm", {})

    out_dir = _output_dir()
    pdf_path = out_dir / f"saas_full_scan_{scan_id}.pdf"

    generate_scan_pdf_enterprise(
        pdf_path,
        scan_meta,
        vm,
    )

    return redirect(
        url_for("scans.download_report", scan_id=scan_id)
    )