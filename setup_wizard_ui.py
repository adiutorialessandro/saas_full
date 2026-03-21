import os

# ==========================================
# 1. AGGIORNAMENTO STEP 1: PROFILAZIONE
# ==========================================
step1_html = """{% extends "base.html" %}
{% block content %}
<style>
    .wizard-container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
    .wizard-header { text-align: center; margin-bottom: 40px; }
    .section-card {
        background: white; border-radius: 16px; padding: 35px;
        margin-bottom: 30px; border: 1px solid #e8eef5;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .section-title { font-weight: 800; font-size: 1.3rem; color: #1a1a2e; margin-bottom: 25px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px;}
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
    .form-group { display: flex; flex-direction: column; gap: 8px; }
    .form-group label { font-weight: 700; color: #334155; font-size: 0.95rem; }
    .form-control { padding: 14px 18px; border: 2px solid #e2e8f0; border-radius: 12px; font-size: 1rem; color: #0f172a; transition: all 0.2s; background: #f8fafc; }
    .form-control:focus { border-color: #38bdf8; background: white; outline: none; box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1); }
</style>

<div class="wizard-container">
    <div class="wizard-header">
        <span class="badge badge-warning" style="margin-bottom: 10px; font-size: 0.8rem; padding: 6px 12px;">STEP 1 DI 3</span>
        <h1 style="font-size: 2.5rem; font-weight: 900; color: #0f172a;">Profilazione Aziendale</h1>
        <p class="muted" style="font-size: 1.1rem; margin-top: 10px;">Definisci il perimetro operativo per allineare gli algoritmi di benchmark.</p>
    </div>

    <form method="POST">
        {{ form.hidden_tag() }}

        <div class="section-card" style="border-top: 5px solid #3b82f6;">
            <div class="section-title"><i class="fas fa-building" style="color: #3b82f6;"></i> Identità e Mercato</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.tipologia_impresa.label }}
                    {{ form.tipologia_impresa(class="form-control") }}
                </div>
                <div class="form-group">
                    {{ form.modello.label }}
                    {{ form.modello(class="form-control") }}
                </div>
                <div class="form-group">
                    {{ form.tipologia_clienti.label }}
                    {{ form.tipologia_clienti(class="form-control") }}
                </div>
            </div>
        </div>

        <div class="section-card" style="border-top: 5px solid #8b5cf6;">
            <div class="section-title"><i class="fas fa-chart-pie" style="color: #8b5cf6;"></i> Dimensioni Operative</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.dimensione.label }}
                    {{ form.dimensione(class="form-control") }}
                </div>
                <div class="form-group">
                    {{ form.dipendenti.label }}
                    {{ form.dipendenti(class="form-control") }}
                </div>
                <div class="form-group">
                    {{ form.fatturato.label }}
                    {{ form.fatturato(class="form-control", placeholder="es. 1.500.000") }}
                </div>
                <div class="form-group">
                    {{ form.area_geografica.label }}
                    {{ form.area_geografica(class="form-control", placeholder="es. Nord Italia") }}
                </div>
            </div>
        </div>

        <div class="section-card" style="border-top: 5px solid #10b981;">
            <div class="section-title"><i class="fas fa-calendar-alt" style="color: #10b981;"></i> Periodo di Analisi</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.mese_riferimento.label }}
                    {{ form.mese_riferimento(class="form-control", placeholder="es. 2026-03") }}
                    <span style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Inserisci l'anno e il mese dei dati che andrai a caricare.</span>
                </div>
            </div>
        </div>

        <div style="margin-top: 40px; text-align: right; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 -10px 30px rgba(0,0,0,0.05);">
            <button type="submit" class="btn-nav-action" style="border:none; cursor:pointer; padding: 16px 45px; font-size: 1.1rem; border-radius: 12px;">
                Avanti allo Step 2 <i class="fas fa-arrow-right"></i>
            </button>
        </div>
    </form>
</div>
{% endblock %}
"""
with open('app/templates/wizard_onboarding.html', 'w') as f:
    f.write(step1_html)

# ==========================================
# 2. AGGIORNAMENTO STEP 2: FINANCIAL DATA
# ==========================================
step2_html = """{% extends "base.html" %}
{% block content %}
<style>
    .wizard-container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
    .wizard-header { text-align: center; margin-bottom: 40px; }
    .section-card {
        background: white; border-radius: 16px; padding: 35px;
        margin-bottom: 30px; border: 1px solid #e8eef5;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .section-title { font-weight: 800; font-size: 1.3rem; color: #1a1a2e; margin-bottom: 25px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px;}
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
    .form-group { display: flex; flex-direction: column; gap: 8px; }
    .form-group label { font-weight: 700; color: #334155; font-size: 0.95rem; }
    .form-control { padding: 14px 18px; border: 2px solid #e2e8f0; border-radius: 12px; font-size: 1rem; color: #0f172a; transition: all 0.2s; background: #f8fafc; }
    .form-control:focus { border-color: #38bdf8; background: white; outline: none; box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1); }
    .help-text { font-size: 0.8rem; color: #64748b; margin-top: 4px; line-height: 1.4; }
</style>

<div class="wizard-container">
    <div class="wizard-header">
        <span class="badge badge-warning" style="margin-bottom: 10px; font-size: 0.8rem; padding: 6px 12px; background: #38bdf8; color: white;">STEP 2 DI 3</span>
        <h1 style="font-size: 2.5rem; font-weight: 900; color: #0f172a;">Dati Finanziari & KPI</h1>
        <p class="muted" style="font-size: 1.1rem; margin-top: 10px;">Inserisci le metriche economiche. Usa 0 se un dato non è disponibile.</p>
    </div>

    <form method="POST">
        {{ form.hidden_tag() }}

        <div class="section-card" style="border-top: 5px solid #10b981;">
            <div class="section-title"><i class="fas fa-wallet" style="color: #10b981;"></i> Liquidità e Sopravvivenza (Runway)</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.cassa_attuale.label }}
                    {{ form.cassa_attuale(class="form-control", placeholder="es. 45000") }}
                    <span class="help-text">Totale della liquidità disponibile oggi sui conti correnti.</span>
                </div>
                <div class="form-group">
                    {{ form.burn_mensile.label }}
                    {{ form.burn_mensile(class="form-control", placeholder="es. 8500") }}
                    <span class="help-text">Soldi "bruciati" al mese. Se l'azienda è in utile, metti 0.</span>
                </div>
            </div>
        </div>

        <div class="section-card" style="border-top: 5px solid #f59e0b;">
            <div class="section-title"><i class="fas fa-chart-line" style="color: #f59e0b;"></i> Conto Economico Mensile</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.incassi_mese.label }}
                    {{ form.incassi_mese(class="form-control", placeholder="es. 25000") }}
                    <span class="help-text">Fatturato incassato nel mese di riferimento.</span>
                </div>
                <div class="form-group">
                    {{ form.costi_fissi_mese.label }}
                    {{ form.costi_fissi_mese(class="form-control", placeholder="es. 12000") }}
                    <span class="help-text">Spese fisse (affitti, stipendi, software) indipendenti dalle vendite.</span>
                </div>
                <div class="form-group">
                    {{ form.margine_lordo_pct.label }}
                    {{ form.margine_lordo_pct(class="form-control", placeholder="es. 65") }}
                    <span class="help-text">La percentuale di incasso che ti resta tolto il costo di erogazione/produzione.</span>
                </div>
            </div>
        </div>

        <div class="section-card" style="border-top: 5px solid #ef4444;">
            <div class="section-title"><i class="fas fa-bullseye" style="color: #ef4444;"></i> Motore Commerciale (Acquisizione)</div>
            <div class="form-grid">
                <div class="form-group">
                    {{ form.leads_mese.label }}
                    {{ form.leads_mese(class="form-control", placeholder="es. 120") }}
                    <span class="help-text">Quanti contatti, richieste o prospect hai generato nel mese?</span>
                </div>
                <div class="form-group">
                    {{ form.clienti_mese.label }}
                    {{ form.clienti_mese(class="form-control", placeholder="es. 15") }}
                    <span class="help-text">Quanti di questi contatti si sono trasformati in clienti paganti?</span>
                </div>
            </div>
        </div>

        <div style="margin-top: 40px; display: flex; justify-content: space-between; align-items: center; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 -10px 30px rgba(0,0,0,0.05);">
            <a href="{{ url_for('wizard.step1') }}" class="btn btn-secondary" style="padding: 12px 30px; text-decoration: none; border-radius: 10px;">
                <i class="fas fa-arrow-left"></i> Indietro
            </a>
            <button type="submit" class="btn-nav-action" style="border:none; cursor:pointer; padding: 16px 45px; font-size: 1.1rem; border-radius: 12px;">
                Avanti allo Step 3 <i class="fas fa-arrow-right"></i>
            </button>
        </div>
    </form>
</div>
{% endblock %}
"""
with open('app/templates/wizard_data.html', 'w') as f:
    f.write(step2_html)

print("✅ Interfacce Step 1 e Step 2 aggiornate con successo al design Premium!")
