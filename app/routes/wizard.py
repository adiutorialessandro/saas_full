import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import EssentialDataForm, OnboardingForm, QuizForm
from ..models.organization import Organization
from ..models.scan import Scan
from ..models.benchmark import SectorBenchmark  # <--- NUOVO IMPORT
from ..services.report_builder import Inputs, build_report
from ..tenant import ensure_current_org_id

bp = Blueprint("wizard", __name__, url_prefix="/wizard")


@bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    ensure_current_org_id()

    form = OnboardingForm()
    if form.validate_on_submit():
        session["onboarding"] = {
            "settore": form.settore.data,
            "modello": form.modello.data,
            "mese_riferimento": form.mese_riferimento.data,
        }
        session.pop("data", None)
        return redirect(url_for("wizard.data"))

    return render_template("wizard_onboarding.html", form=form)


@bp.route("/data", methods=["GET", "POST"])
@login_required
def data():
    ensure_current_org_id()

    if "onboarding" not in session:
        return redirect(url_for("wizard.onboarding"))

    form = EssentialDataForm()
    if form.validate_on_submit():
        # Salviamo i dati puliti (form.data include anche campi extra come submit)
        session["data"] = {k: v for k, v in form.data.items() if k not in ['csrf_token', 'submit']}
        return redirect(url_for("wizard.quiz"))

    return render_template("wizard_data.html", form=form)


@bp.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    org_id = ensure_current_org_id()

    if "onboarding" not in session:
        return redirect(url_for("wizard.onboarding"))

    form = QuizForm()
    if form.validate_on_submit():
        raw = [int(getattr(form, f"q{i}").data) for i in range(1, 11)]
        quiz_risk = [1.0 - ((v - 1.0) / 4.0) for v in raw]

        ob = session["onboarding"]
        data = session.get("data", {}) or {}

        # 1. Recupero del Benchmark dal Database basato sul settore
        # Cerchiamo il match esatto con il settore salvato in sessione
        bench = SectorBenchmark.query.filter_by(sector_name=ob["settore"]).first()

        # 2. Preparazione Input per il calcolo
        inp = Inputs(
            settore=ob["settore"],
            modello=ob["modello"],
            mese_riferimento=ob["mese_riferimento"],
            quiz_risk=quiz_risk,
            cassa_attuale=data.get("cassa_attuale"),
            burn_mensile=data.get("burn_mensile"),
            incassi_mese=data.get("incassi_mese"),
            costi_fissi_mese=data.get("costi_fissi_mese"),
            margine_lordo_pct=data.get("margine_lordo_pct"),
            leads_mese=data.get("leads_mese"),
            clienti_mese=data.get("clienti_mese"),
        )

        # 3. Generazione Report con Benchmark (Passiamo l'oggetto bench)
        report = build_report(inp, bench=bench)

        # 4. Controllo piano / limite scansioni
        org = Organization.query.get(org_id)
        if not org:
            flash("Organizzazione non trovata.")
            return redirect(url_for("scans.dashboard"))

        if not org.plan:
            flash("Nessun piano associato all'azienda.")
            return redirect(url_for("scans.dashboard"))

        current_scans = Scan.query.filter_by(org_id=org.id).count()
        if org.plan.scan_limit != -1 and current_scans >= org.plan.scan_limit:
            flash("Limite scansioni raggiunto per il piano attuale.")
            return redirect(url_for("scans.dashboard"))

        # 5. Salvataggio Scan nel DB
        s = Scan(
            org_id=org_id,
            user_id=current_user.id,
            settore=ob["settore"],
            modello=ob["modello"],
            mese_riferimento=ob["mese_riferimento"],
            report_json=json.dumps(report, ensure_ascii=False),
            created_at=datetime.utcnow(),
        )

        db.session.add(s)
        db.session.commit()

        # Pulizia sessione dopo la creazione dello scan
        session.pop("onboarding", None)
        session.pop("data", None)

        flash("Analisi completata con successo.")
        return render_template("scan_processing.html", scan=s)

    return render_template("quiz.html", form=form)