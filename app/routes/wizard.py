import json
import logging
from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_login import login_required, current_user

from app.forms import OnboardingForm, EssentialDataForm, QuizForm, RetailDataForm
from app.models.scan import Scan
from app.models.benchmark import SectorBenchmark
from app.extensions import db

from app.services.diagnostic_engine import generate_deterministic_report, Inputs
from app.services.retail_engine import generate_retail_report, RetailInputs

# 🛡️ IMPORTS AGGIUNTI PER IL PAYWALL E LA SICUREZZA TENANT
from app.tenant import ensure_current_org_id
from app.models.organization import Organization

logger = logging.getLogger(__name__)
bp = Blueprint('wizard', __name__, url_prefix='/wizard')

@bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():
    # 🧱 IL PAYWALL (Blindato)
    org_id = ensure_current_org_id()
    org = Organization.query.get(org_id)
    
    if org and org.plan and org.plan.scan_limit != -1:
        scan_count = Scan.query.filter_by(org_id=org_id).count()
        
        if scan_count >= org.plan.scan_limit:
            # Messaggio dinamico che fa capire all'utente il suo limite
            flash(f"Hai raggiunto il limite di {org.plan.scan_limit} report previsto dal tuo piano {org.plan.name}. Fai l'upgrade per continuare l'analisi.", "warning")
            # 🚀 Reindirizzamento corretto alla rotta principale dei prezzi
            return redirect(url_for('pricing'))

    # Se passa il controllo, mostra il form normale
    form = OnboardingForm()
    if form.validate_on_submit():
        session['wizard_step1'] = {
            'tipologia_impresa': form.tipologia_impresa.data,
            'modello': form.modello.data,
            'mese_riferimento': form.mese_riferimento.data
        }
        return redirect(url_for('wizard.step2'))
    return render_template('wizard_onboarding.html', form=form)

@bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    if 'wizard_step1' not in session:
        return redirect(url_for('wizard.step1'))
        
    settore = session['wizard_step1'].get('tipologia_impresa', '')
    modello = session['wizard_step1'].get('modello', '')
    
    # BIVIO: Se è un business fisico o B2C, mandalo al form Retail
    if modello == 'B2C' or settore in ['Retail', 'Ho.Re.Ca.', 'Saloni', 'Ristorazione', 'Estetica']:
        form = RetailDataForm()
        if form.validate_on_submit():
            session['wizard_step2_retail'] = {
                'ricavi_dichiarati': form.ricavi_dichiarati.data,
                'incassi_reali': form.incassi_reali.data,
                'costi_personale': form.costi_personale.data,
                'costi_struttura': form.costi_struttura.data,
                'costi_prodotti': form.costi_prodotti.data,
                'compenso_titolare': form.compenso_titolare.data,
                'ticket_medio': form.ticket_medio.data,
                'clienti_mese': form.clienti_mese.data
            }
            return redirect(url_for('wizard.generate_retail')) 
        return render_template('wizard_retail_data.html', form=form)
        
    else:
        # VECCHIO FLUSSO B2B / SAAS
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
    if 'wizard_step2' not in session: return redirect(url_for('wizard.step2'))
    form = QuizForm()
    if form.validate_on_submit():
        s1, s2 = session['wizard_step1'], session['wizard_step2']
        inp = Inputs(
            settore=s1.get('tipologia_impresa'), modello=s1.get('modello'), mese_riferimento=s1.get('mese_riferimento'),
            dimensione='', dipendenti='', area_geografica='', fatturato='', tipologia_clienti='',
            cassa_attuale=s2.get('cassa_attuale'), burn_mensile=s2.get('burn_mensile'),
            incassi_mese=s2.get('incassi_mese'), costi_fissi_mese=s2.get('costi_fissi_mese'),
            margine_lordo_pct=s2.get('margine_lordo_pct'), leads_mese=s2.get('leads_mese'),
            clienti_mese=s2.get('clienti_mese'), quiz_responses={}, quiz_risk=[]
        )
        bench = SectorBenchmark.query.filter_by(sector_name=inp.settore).first()
        report_data = generate_deterministic_report(inp, bench)
        
        new_scan = Scan(user_id=current_user.id, org_id=current_user.primary_org_id(), settore=inp.settore, modello=inp.modello, mese_riferimento=inp.mese_riferimento, report_json=json.dumps(report_data), raw_data="{}")
        db.session.add(new_scan); db.session.commit()
        session.pop('wizard_step1', None); session.pop('wizard_step2', None)
        flash("Scansione strategica completata!", "success")
        return redirect(url_for('scans.view_scan', scan_id=new_scan.id))
    return render_template('quiz.html', form=form)

@bp.route('/generate_retail')
@login_required
def generate_retail():
    if 'wizard_step1' not in session or 'wizard_step2_retail' not in session: return redirect(url_for('wizard.step1'))
    s1, s2 = session['wizard_step1'], session['wizard_step2_retail']
    inp = RetailInputs(
        settore=s1.get('tipologia_impresa'), mese_riferimento=s1.get('mese_riferimento'),
        ricavi_dichiarati=s2.get('ricavi_dichiarati', 0), incassi_reali_stimati=s2.get('incassi_reali', 0),
        costi_personale=s2.get('costi_personale', 0), costi_struttura=s2.get('costi_struttura', 0),
        costi_prodotti=s2.get('costi_prodotti', 0), compenso_titolare=s2.get('compenso_titolare'),
        ticket_medio=s2.get('ticket_medio'), clienti_mese=s2.get('clienti_mese')
    )
    report_data = generate_retail_report(inp)
    
    new_scan = Scan(user_id=current_user.id, org_id=current_user.primary_org_id(), settore=inp.settore, modello="Local/Retail", mese_riferimento=inp.mese_riferimento, report_json=json.dumps(report_data), raw_data="{}")
    db.session.add(new_scan); db.session.commit()
    session.pop('wizard_step1', None); session.pop('wizard_step2_retail', None)
    flash("Analisi Local Business generata con successo!", "success")
    return redirect(url_for('scans.view_scan', scan_id=new_scan.id))
