import json
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required
from ..extensions import db
from ..forms import EssentialDataForm, OnboardingForm, QuizForm
from ..models.organization import Organization
from ..models.scan import Scan
from ..models.benchmark import SectorBenchmark
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
            "settore": form.tipologia_impresa.data,
            "modello": form.modello.data,
            "dimensione": form.dimensione.data,
            "dipendenti": form.dipendenti.data,
            "area_geografica": form.area_geografica.data,
            "fatturato": form.fatturato.data,
            "tipologia_clienti": form.tipologia_clienti.data,
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
        try:
            raw = [int(getattr(form, f"q{i}").data) for i in range(1, 11)]
            quiz_risk = [1.0 - ((v - 1.0) / 4.0) for v in raw]

            ob = session["onboarding"]
            data = session.get("data", {}) or {}

            bench = SectorBenchmark.query.filter_by(sector_name=ob.get("settore")).first()

            inp = Inputs(
                settore=ob.get("settore", "Generico"),
                modello=ob.get("modello", "B2B"),
                mese_riferimento=ob.get("mese_riferimento", ""),
                quiz_risk=quiz_risk,
                dimensione=ob.get("dimensione"),
                dipendenti=ob.get("dipendenti"),
                area_geografica=ob.get("area_geografica"),
                fatturato=ob.get("fatturato"),
                tipologia_clienti=ob.get("tipologia_clienti"),
                cassa_attuale=data.get("cassa_attuale"),
                burn_mensile=data.get("burn_mensile"),
                incassi_mese=data.get("incassi_mese"),
                costi_fissi_mese=data.get("costi_fissi_mese"),
                margine_lordo_pct=data.get("margine_lordo_pct"),
                leads_mese=data.get("leads_mese"),
                clienti_mese=data.get("clienti_mese"),
            )

            report = build_report(inp, bench=bench)

            org = Organization.query.get(org_id)
            if not org or not org.plan:
                flash("Organizzazione o piano non trovati.")
                return redirect(url_for("scans.dashboard"))

            current_scans = Scan.query.filter_by(org_id=org.id).count()
            if org.plan.scan_limit != -1 and current_scans >= org.plan.scan_limit:
                flash("Limite scansioni raggiunto per il piano attuale.")
                return redirect(url_for("scans.dashboard"))

            s = Scan(
                org_id=org_id,
                user_id=current_user.id,
                settore=ob.get("settore", "Generico"),
                modello=ob.get("modello", "B2B"),
                mese_riferimento=ob.get("mese_riferimento", ""),
                report_json=json.dumps(report, ensure_ascii=False),
                created_at=datetime.utcnow(),
            )

            db.session.add(s)
            db.session.commit()

            session.pop("onboarding", None)
            session.pop("data", None)

            flash("Analisi completata con successo.")
            return render_template("scan_processing.html", scan=s)

        except Exception as e:
            # QUESTO È IL SALVAVITA: Se qualcosa si rompe, te lo scrive a schermo senza farti la pagina 500!
            import traceback
            print("ERRORE CRITICO NEL QUIZ:", traceback.format_exc())
            flash(f"Errore tecnico durante il calcolo: {str(e)}", "danger")
            return redirect(url_for("wizard.quiz"))

    return render_template("quiz.html", form=form)
