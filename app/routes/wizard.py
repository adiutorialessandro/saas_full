"""
SaaS Full - Wizard Routes & Report Generation Trigger
Gestisce l'inserimento dati in 3 step e innesca la generazione del report finale.
"""
import json
import logging
from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_login import login_required, current_user

from app.forms import OnboardingForm, EssentialDataForm, QuizForm
from app.models.scan import Scan
from app.models.benchmark import SectorBenchmark
from app.services.report_builder import build_report, Inputs
from app.extensions import db

logger = logging.getLogger(__name__)
bp = Blueprint('wizard', __name__, url_prefix='/wizard')

@bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():

    # --- SAAS LIMIT CHECK (PAYWALL) ---
    from app.models.scan import Scan
    org = current_user.current_org
    if org and org.plan:
        if org.plan.scan_limit != -1:
            scan_count = Scan.query.filter_by(org_id=org.id).count()
            if scan_count >= org.plan.scan_limit:
                flash("Hai raggiunto il limite di scansioni gratuite del tuo piano. Fai l'upgrade per sbloccare nuove analisi.", "warning")
                return redirect(url_for('billing.pricing'))
    # ----------------------------------

    form = OnboardingForm()
    if form.validate_on_submit():
        session['wizard_step1'] = {
            'tipologia_impresa': form.tipologia_impresa.data,
            'modello': form.modello.data,
            'dimensione': form.dimensione.data,
            'dipendenti': form.dipendenti.data,
            'area_geografica': form.area_geografica.data,
            'fatturato': form.fatturato.data,
            'tipologia_clienti': form.tipologia_clienti.data,
            'mese_riferimento': form.mese_riferimento.data
        }
        return redirect(url_for('wizard.step2'))
    return render_template('wizard_onboarding.html', form=form)


@bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    if 'wizard_step1' not in session:
        return redirect(url_for('wizard.step1'))
        
    form = EssentialDataForm()
    if form.validate_on_submit():
        session['wizard_step2'] = {
            'cassa_attuale': form.cassa_attuale.data,
            'burn_mensile': form.burn_mensile.data,
            'incassi_mese': form.incassi_mese.data,
            'costi_fissi_mese': form.costi_fissi_mese.data,
            'margine_lordo_pct': form.margine_lordo_pct.data,
            'leads_mese': form.leads_mese.data,
            'clienti_mese': form.clienti_mese.data
        }
        return redirect(url_for('wizard.step3'))
    return render_template('wizard_data.html', form=form)


@bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    if 'wizard_step2' not in session:
        return redirect(url_for('wizard.step2'))
        
    form = QuizForm()
    if form.validate_on_submit():
        s1 = session['wizard_step1']
        s2 = session['wizard_step2']
        
        # 1. Raccolta dati McKinsey 7S
        s3 = {
            'chiarezza_obiettivi': form.chiarezza_obiettivi.data,
            'condivisione_valori': form.condivisione_valori.data,
            'efficacia_sistemi': form.efficacia_sistemi.data,
            'velocita_decisionale': form.velocita_decisionale.data,
            'apertura_cambiamento': form.apertura_cambiamento.data,
            'apprendimento_errore': form.apprendimento_errore.data,
            'fiducia_leadership': form.fiducia_leadership.data,
            'clima_team': form.clima_team.data,
        }
        
        # 2. Impacchettamento per l'Orchestratore
        inp = Inputs(
            settore=s1.get('tipologia_impresa'),
            modello=s1.get('modello'),
            mese_riferimento=s1.get('mese_riferimento'),
            dimensione=s1.get('dimensione'),
            dipendenti=s1.get('dipendenti'),
            area_geografica=s1.get('area_geografica'),
            fatturato=s1.get('fatturato'),
            tipologia_clienti=s1.get('tipologia_clienti'),
            
            cassa_attuale=s2.get('cassa_attuale'),
            burn_mensile=s2.get('burn_mensile'),
            incassi_mese=s2.get('incassi_mese'),
            costi_fissi_mese=s2.get('costi_fissi_mese'),
            margine_lordo_pct=s2.get('margine_lordo_pct'),
            leads_mese=s2.get('leads_mese'),
            clienti_mese=s2.get('clienti_mese'),
            
            quiz_responses=s3,
            quiz_risk=[]  # Fallback legacy
        )

        try:
            # 3. Estrazione Benchmark ed Esecuzione del Motore
            bench = SectorBenchmark.query.filter_by(sector_name=inp.settore).first()
            generated_report = build_report(inp, bench)

            # 4. Salvataggio nel Database
            new_scan = Scan(
                user_id=current_user.id,
                org_id=current_user.primary_org_id(),
                settore=inp.settore,
                modello=inp.modello,
                mese_riferimento=inp.mese_riferimento,
                report_json=json.dumps(generated_report),
                raw_data=json.dumps({"step1": s1, "step2": s2, "step3": s3})
            )
            
            # (Opzionale) Salva gli score di sintesi direttamente nel DB per i grafici
            triade_state = generated_report.get('triade', {}).get('state', {})
            new_scan.triad_index = triade_state.get('maturity_score')
            new_scan.finance_score = generated_report.get('triade', {}).get('risks', {}).get('cash')
            
            db.session.add(new_scan)
            db.session.commit()
            
            # 5. Pulizia Sessione e Redirect
            session.pop('wizard_step1', None)
            session.pop('wizard_step2', None)
            
            flash("Scansione strategica completata con successo!", "success")
            return redirect(url_for('scans.view_scan', scan_id=new_scan.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore critico durante la generazione del report: {str(e)}", exc_info=True)
            flash("Si è verificato un errore durante l'elaborazione del report. Contatta l'assistenza.", "danger")
            return redirect(url_for('wizard.step3'))
            
    return render_template('quiz.html', form=form)