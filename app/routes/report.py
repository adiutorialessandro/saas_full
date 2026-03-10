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

    # Estraiamo la triade dal JSON generato dal service
    triade = report.get("triade", {}) if isinstance(report, dict) else {}
    vm = triade if isinstance(triade, dict) else {}

    # --- INIZIALIZZAZIONE DEFAULT PER SICUREZZA ---
    vm.setdefault("meta", {})  # Qui dentro ora ci sono i benchmark!
    vm.setdefault("state", {})
    vm.setdefault("risks", {})
    vm.setdefault("kpi", {})
    vm.setdefault("indicators", [])
    vm.setdefault("alerts", [])
    vm.setdefault("decisions", {})
    vm.setdefault("action_plan", [])
    vm.setdefault("plan_tasks", [])

    # Default per la sezione Meta (Settore e Benchmark)
    vm["meta"].setdefault("settore", scan.settore)
    vm["meta"].setdefault("benchmark_settore", None)

    # Default per lo State
    vm["state"].setdefault("overall", "GIALLO")
    vm["state"].setdefault("overall_score", 50)
    vm["state"].setdefault("summary", "Analisi completata.")
    vm["state"].setdefault("confidence", 50)
    vm["state"].setdefault("maturity_label", "Maturità in fase di calcolo")

    # Default Rischi
    vm["risks"].setdefault("cash", 0.5)
    vm["risks"].setdefault("margini", 0.5)
    vm["risks"].setdefault("acq", 0.5)

    # Default KPI
    vm["kpi"].setdefault("runway_mesi", None)
    vm["kpi"].setdefault("break_even_ratio", None)
    vm["kpi"].setdefault("conversione", None)
    vm["kpi"].setdefault("margine_pct", None)

    scan_meta = {
        "id": scan.id,
        "settore": scan.settore,
        "modello": scan.modello,
        "mese": scan.mese_riferimento,
        "created_at": scan.created_at,
    }

    # --- GESTIONE STORICO (HISTORY) ---
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
            t = r.get("triade", {})
            st = t.get("state", {})
            rk = t.get("risks", {})

            # Usiamo triad_index della colonna DB o quello nel JSON
            score = s.triad_index if s.triad_index is not None else st.get("overall_score", 50)

            history.append({
                "id": s.id,
                "label": s.mese_riferimento or f"Scan {s.id}",
                "overall_score": score,
                "cash": round(float(rk.get("cash", 0.5)) * 100, 1),
                "margini": round(float(rk.get("margini", 0.5)) * 100, 1),
                "acq": round(float(rk.get("acq", 0.5)) * 100, 1),
            })
        except Exception:
            continue

    # --- CALCOLO DELTA (CONFRONTO CON SCAN PRECEDENTE) ---
    delta = {"score": None, "cash": None, "margini": None, "acq": None}

    if len(history) >= 2:
        curr, prev = history[-1], history[-2]
        delta["score"] = round(float(curr["overall_score"]) - float(prev["overall_score"]), 1)
        delta["cash"] = round(float(curr["cash"]) - float(prev["cash"]), 1)
        delta["margini"] = round(float(curr["margini"]) - float(prev["margini"]), 1)
        delta["acq"] = round(float(curr["acq"]) - float(prev["acq"]), 1)

    # Generazione payload dinamico per l'header (titolo e sottotitolo report)
    header_payload = report_header_payload(vm, delta)

    return render_template(
        "report_full.html",
        scan=scan,
        scan_meta=scan_meta,
        vm=vm,  # vm['meta']['benchmark_settore'] è ora disponibile nel template!
        history=history,
        delta=delta,
        header_payload=header_payload,
    )

@bp.get("/api/triad-trend")
@login_required
def triad_trend():
    # ... (Resto del codice api/triad-trend rimane identico) ...
    org_id = ensure_current_org_id()
    scans = Scan.query.filter_by(org_id=org_id).order_by(Scan.created_at.asc()).all()
    # Logica per grafici Chart.js...
    return jsonify({"labels": [], "values": []}) # (Omettiamo per brevità, resta uguale)